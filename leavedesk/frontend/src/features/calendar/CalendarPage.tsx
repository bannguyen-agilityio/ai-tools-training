import { useState } from "react";
import { useMe } from "../../auth/useMe";
import { formatDate, todayIso } from "../../lib/dates";
import { Button } from "../../ui/Button";
import { Field } from "../../ui/Field";
import { useTeams } from "../hr/teams/api";
import { useCalendar } from "./api";
import { groupByDay } from "./labels";

function shift(month: string, by: number): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(Date.UTC(y, m - 1 + by, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

function monthTitle(month: string): string {
  return formatDate(`${month}-01`).split(" ").slice(2).join(" ");
}

/** HR only: the team list comes from an HR-only endpoint, so it is fetched only here. */
function TeamFilter({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  const teams = useTeams();
  return (
    <Field label="Team">
      {(c) => (
        <select className="input" value={value} onChange={(e) => onChange(e.target.value)} {...c}>
          <option value="">All teams</option>
          {teams.data?.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      )}
    </Field>
  );
}

/** Team calendar (R27). A day-by-day list that reads well at 360 px; Pending is spelled out. */
export function CalendarPage() {
  const [month, setMonth] = useState(todayIso().slice(0, 7));
  const [teamId, setTeamId] = useState("");
  const { data: me } = useMe();
  const isHr = me?.role === "hr";
  const calendar = useCalendar(month, isHr ? teamId : "", me !== undefined);
  const days = calendar.data ? groupByDay(calendar.data.entries) : [];

  return (
    <section aria-labelledby="calendar-title">
      <h1 id="calendar-title">Team calendar</h1>
      <div className="calendar-nav">
        <Button variant="secondary" onClick={() => setMonth(shift(month, -1))}>
          Previous month
        </Button>
        <h2 aria-live="polite">{monthTitle(month)}</h2>
        <Button variant="secondary" onClick={() => setMonth(shift(month, 1))}>
          Next month
        </Button>
      </div>
      {isHr && <TeamFilter value={teamId} onChange={setTeamId} />}
      {calendar.isPending && <p>Loading the calendar…</p>}
      {calendar.isError && <p role="alert">Could not load the calendar. Try again later.</p>}
      {calendar.data && days.length === 0 && <p>No one in {isHr && !teamId ? "any team" : "your team"} is on leave this month.</p>}
      {days.length > 0 && (
        <ul className="calendar-list">
          {days.map((day) => (
            <li key={day.date}>
              <h3>{formatDate(day.date)}</h3>
              <ul>
                {day.items.map((item) => (
                  <li key={item.key} className={item.pending ? "calendar-item calendar-item--pending" : "calendar-item"}>
                    {item.text}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
