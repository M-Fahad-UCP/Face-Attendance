"""
Authentication layer.

- SQLite storage in database/users.db
- bcrypt password hashing
- Role-based access (admin / user)
- Single admin account, auto-created on first startup
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

import bcrypt

from src.config import (
    DEFAULT_ADMIN_FULLNAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    ROLE_ADMIN,
    ROLE_USER,
    USERS_DB_PATH,
    ensure_directories,
)
from src.logger import get_logger

log = get_logger("auth")


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class User:
    id: int
    username: str
    full_name: str
    role: str
    department: str = ""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row factory + foreign keys on."""
    ensure_directories()
    conn = sqlite3.connect(str(USERS_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the users table and the default admin row (idempotent)."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                full_name   TEXT    NOT NULL,
                password    BLOB    NOT NULL,
                role        TEXT    NOT NULL CHECK (role IN ('admin', 'user')),
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_single_admin
            ON users(role) WHERE role = 'admin';
            """
        )
        _ensure_user_columns(conn)

    if not _admin_exists():
        _create_default_admin()


def _ensure_user_columns(conn: sqlite3.Connection) -> None:
    """Apply lightweight schema migrations (SQLite)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "department" not in cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN department TEXT NOT NULL DEFAULT ''"
        )
        log.info("Added users.department column.")


def _admin_exists() -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE role = ?", (ROLE_ADMIN,)
        ).fetchone()
    return bool(row and row["c"] > 0)


def _create_default_admin() -> None:
    pw_hash = bcrypt.hashpw(
        DEFAULT_ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
    )
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, full_name, password, role) "
                "VALUES (?, ?, ?, ?)",
                (
                    DEFAULT_ADMIN_USERNAME,
                    DEFAULT_ADMIN_FULLNAME,
                    pw_hash,
                    ROLE_ADMIN,
                ),
            )
        log.info("Default admin account created: %s", DEFAULT_ADMIN_USERNAME)
    except sqlite3.IntegrityError:
        # Race-condition safety – another worker may have created it.
        log.info("Admin already exists, skipping creation.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def _row_to_user(row: sqlite3.Row) -> User:
    dept = ""
    try:
        dept = str(row["department"] or "")
    except (KeyError, IndexError):
        pass
    return User(
        id=row["id"],
        username=row["username"],
        full_name=row["full_name"],
        role=row["role"],
        department=dept,
    )


def get_user_by_username(username: str) -> Optional[User]:
    """Return a lightweight User row (no password) or None."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, role, department FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_user(row)


def get_user_by_id(user_id: int) -> Optional[User]:
    """Return a User by primary key, or None if deleted."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, role, department FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()
    if row is None:
        return None
    return _row_to_user(row)


def user_exists(username: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
    return row is not None


def create_user(
    username: str, full_name: str, password: str, *, department: str = ""
) -> User:
    """
    Create a normal (client) user. Admin role is NOT exposed via this API –
    only the bootstrap default admin row may have role='admin'.

    Raises
    ------
    ValueError if the username already exists.
    """
    if user_exists(username):
        raise ValueError("Username already exists.")

    dept = (department or "").strip()
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, full_name, password, role, department) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, full_name, pw_hash, ROLE_USER, dept),
        )
        user_id = cur.lastrowid

    log.info("Created user: %s (id=%s)", username, user_id)
    return User(
        id=user_id,
        username=username,
        full_name=full_name,
        role=ROLE_USER,
        department=dept,
    )


def authenticate(username: str, password: str) -> Optional[User]:
    """Return a User on success, None on bad password, raise on unknown user."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, password, role, department FROM users "
            "WHERE username = ?",
            (username,),
        ).fetchone()

    if row is None:
        raise LookupError("Account not found.")

    stored_hash = row["password"]
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return None

    return _row_to_user(row)


def list_users(role: Optional[str] = None) -> list[User]:
    query = "SELECT id, username, full_name, role, department FROM users"
    params: tuple = ()
    if role is not None:
        query += " WHERE role = ?"
        params = (role,)
    query += " ORDER BY username ASC"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    return [_row_to_user(r) for r in rows]


def delete_user(username: str) -> bool:
    """Delete a non-admin user. Admin accounts cannot be deleted here."""
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM users WHERE username = ? AND role = ?",
            (username, ROLE_USER),
        )
        deleted = cur.rowcount > 0
    if deleted:
        log.info("Deleted user: %s", username)
    return deleted


def change_password(username: str, new_password: str) -> bool:
    pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (pw_hash, username),
        )
        ok = cur.rowcount > 0
    if ok:
        log.info("Password changed for user: %s", username)
    return ok
