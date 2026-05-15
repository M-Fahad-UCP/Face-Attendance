"use client";

import { useCallback, useEffect, useState } from "react";
import { api, apiBlob } from "@/lib/api";
import type { AttendanceRecord } from "@/lib/types";
import { Button, Input, Label } from "./ui";
import { useAuth } from "@/lib/auth-context";

export function ReportsTable() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [q, setQ] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [todayOnly, setTodayOnly] = useState(false);
  const [department] = useState("(All)");
  const [memberFilter, setMemberFilter] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    if (todayOnly) params.set("today_only", "true");
    if (isAdmin && department !== "(All)") params.set("department", department);
    if (isAdmin && memberFilter) params.set("username", memberFilter);
    api<{ records: AttendanceRecord[] }>(`/api/attendance?${params}`)
      .then((r) => setRecords(r.records))
      .catch(console.error);
  }, [q, dateFrom, dateTo, todayOnly, department, memberFilter, isAdmin]);

  useEffect(() => {
    load();
  }, [load]);

  async function downloadCsv() {
    const blob = await apiBlob("/api/attendance/export/csv");
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "attendance_export.csv";
    a.click();
  }

  async function downloadExcel() {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    if (todayOnly) params.set("today_only", "true");
    const blob = await apiBlob(`/api/attendance/export/excel?${params}`);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "attendance_filtered.xlsx";
    a.click();
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Reports</h1>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <Label>Search</Label>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, date…" />
        </div>
        <div>
          <Label>From</Label>
          <Input value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} placeholder="YYYY-MM-DD" />
        </div>
        <div>
          <Label>To</Label>
          <Input value={dateTo} onChange={(e) => setDateTo(e.target.value)} placeholder="YYYY-MM-DD" />
        </div>
        {isAdmin && (
          <div>
            <Label>Member username</Label>
            <Input value={memberFilter} onChange={(e) => setMemberFilter(e.target.value)} />
          </div>
        )}
      </div>
      <label className="mt-2 flex items-center gap-2 text-sm">
        <input type="checkbox" checked={todayOnly} onChange={(e) => setTodayOnly(e.target.checked)} />
        Today only
      </label>
      <Button className="mt-3" onClick={load}>
        Apply filters
      </Button>
      <div className="mt-4 flex gap-2">
        <Button variant="secondary" onClick={downloadCsv}>
          Export full CSV
        </Button>
        <Button variant="secondary" onClick={downloadExcel}>
          Export filtered Excel
        </Button>
      </div>
      <div className="mt-4 overflow-x-auto rounded-lg border bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-2">Member</th>
              <th className="p-2">Name</th>
              {isAdmin && <th className="p-2">Department</th>}
              <th className="p-2">Date</th>
              <th className="p-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r, i) => (
              <tr key={i} className="border-t">
                <td className="p-2">{r.username}</td>
                <td className="p-2">{r.full_name}</td>
                {isAdmin && <td className="p-2">{r.department}</td>}
                <td className="p-2">{r.date}</td>
                <td className="p-2">{r.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!records.length && (
          <p className="p-4 text-center text-slate-500">No matching records.</p>
        )}
      </div>
    </div>
  );
}
