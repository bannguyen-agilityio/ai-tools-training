import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../../ui/Button";
import { Field } from "../../../ui/Field";
import { daysText, rangeText, statusText, TYPE_LABEL } from "../../requests/format";
import { useEmployees } from "../employees/api";
import { useTeams } from "../teams/api";
import { NO_FILTERS, useAllLeave, type LeaveFilters } from "./api";

/** HR: All leave (R25). Approved by default; real types are shown. */
export function AllLeavePage() {
  const [filters, setFilters] = useState<LeaveFilters>(NO_FILTERS);
  const leave = useAllLeave(filters);
  const employees = useEmployees();
  const teams = useTeams();
  const set = (key: keyof LeaveFilters) => (value: string) => setFilters((f) => ({ ...f, [key]: value }));
  const rows = leave.data?.pages.flatMap((p) => p.items) ?? [];
  const invalidRange = filters.from !== "" && filters.to !== "" && filters.to < filters.from;

  return (
    <section aria-labelledby="all-leave-title">
      <h1 id="all-leave-title">All leave</h1>
      <form className="filters" aria-label="Filter leave" onSubmit={(e) => e.preventDefault()}>
        <Field label="Status">
          {(c) => (
            <select className="input" value={filters.status} onChange={(e) => set("status")(e.target.value)} {...c}>
              <option value="approved">Approved</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
              <option value="cancelled">Cancelled</option>
            </select>
          )}
        </Field>
        <Field label="From">
          {(c) => <input className="input" type="date" value={filters.from} onChange={(e) => set("from")(e.target.value)} {...c} />}
        </Field>
        <Field label="To" error={invalidRange ? "The end is before the start." : undefined}>
          {(c) => <input className="input" type="date" value={filters.to} onChange={(e) => set("to")(e.target.value)} {...c} />}
        </Field>
        <Field label="Employee">
          {(c) => (
            <select className="input" value={filters.employee_id} onChange={(e) => set("employee_id")(e.target.value)} {...c}>
              <option value="">Everyone</option>
              {employees.data?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field label="Team">
          {(c) => (
            <select className="input" value={filters.team_id} onChange={(e) => set("team_id")(e.target.value)} {...c}>
              <option value="">All teams</option>
              {teams.data?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field label="Type">
          {(c) => (
            <select className="input" value={filters.type} onChange={(e) => set("type")(e.target.value)} {...c}>
              <option value="">All types</option>
              {Object.entries(TYPE_LABEL).map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Button variant="secondary" onClick={() => setFilters(NO_FILTERS)}>
          Clear filters
        </Button>
      </form>

      {leave.isPending && <p>Loading leave…</p>}
      {leave.isError && <p role="alert">Could not load the leave list. Try again later.</p>}
      {leave.data && rows.length === 0 && <p>No leave matches these filters.</p>}
      {rows.length > 0 && (
        <table className="leave-table">
          <caption className="visually-hidden">Leave, earliest first</caption>
          <thead>
            <tr>
              <th scope="col">Employee</th>
              <th scope="col">Dates</th>
              <th scope="col">Type</th>
              <th scope="col">Days</th>
              <th scope="col">Status</th>
              <th scope="col">Note</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <th scope="row" data-label="Employee">
                  <Link to={`/requests/${r.id}`}>{r.employee_name}</Link>
                </th>
                <td data-label="Dates">{rangeText(r)}</td>
                <td data-label="Type">{TYPE_LABEL[r.leave_type]}</td>
                <td data-label="Days">{daysText(r.working_days)}</td>
                <td data-label="Status">{statusText(r.status)}</td>
                <td data-label="Note">{r.note ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {leave.hasNextPage && (
        <Button variant="secondary" onClick={() => void leave.fetchNextPage()} disabled={leave.isFetchingNextPage}>
          Show more
        </Button>
      )}
    </section>
  );
}
