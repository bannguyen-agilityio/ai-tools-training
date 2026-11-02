import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../../components/ui/Button";
import { Field } from "../../../components/ui/Field";
import { DataList } from "../../../components/ui/DataList";
import { DaysText } from "../../../components/ui/DateText";
import { LeaveTypeTag } from "../../../components/ui/LeaveTypeTag";
import { PageHeader } from "../../../components/ui/Card";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { rangeText, TYPE_LABEL } from "../../requests/format";
import { useEmployees } from "../employees/api";
import { useTeams } from "../teams/api";
import { NO_FILTERS, useAllLeave, type LeaveFilters } from "./api";
import { Alert, EmptyState, Loading, Skeleton } from "../../../components/ui/Feedback";

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
    <section aria-label="All leave">
      <PageHeader title="All leave" />
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

      {leave.isPending && <Loading label="Loading leave…"><Skeleton className="skeleton--row" /></Loading>}
      {leave.isError && <Alert tone="danger">Could not load the leave list. Try again later.</Alert>}
      {leave.data && rows.length === 0 && <EmptyState title="No leave matches these filters." />}
      {rows.length > 0 && (
        <div className="card">
          <DataList
            caption="Leave, earliest first"
            rows={rows}
            rowKey={(r) => r.id}
            columns={[
              { key: "emp", header: "Employee", primary: true, cell: (r) => <Link to={`/requests/${r.id}`}>{r.employee_name}</Link> },
              { key: "dates", header: "Dates", cell: (r) => rangeText(r) },
              { key: "type", header: "Type", cell: (r) => <LeaveTypeTag type={r.leave_type} /> },
              { key: "days", header: "Days", numeric: true, cell: (r) => <DaysText value={r.working_days} /> },
              { key: "status", header: "Status", numeric: true, cell: (r) => <StatusBadge status={r.status} /> },
              { key: "note", header: "Note", cell: (r) => r.note ?? "" },
            ]}
          />
        </div>
      )}
      {leave.hasNextPage && (
        <Button variant="secondary" onClick={() => void leave.fetchNextPage()} disabled={leave.isFetchingNextPage}>
          Show more
        </Button>
      )}
    </section>
  );
}
