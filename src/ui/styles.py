"""Load global CSS once per run (theme follows Streamlit Settings → Theme)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import BASE_DIR

_CSS_PATH = BASE_DIR / "styles.css"


def inject_global_styles() -> None:
    """Inject ``styles.css`` — dark/light follows the app theme from the Streamlit menu."""
    try:
        css = _CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        css = "/* styles.css missing */"
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
