import { useState } from "react";
import { todayIso } from "../../../lib/dates";
import { Field } from "../../../ui/Field";

function previousMonth(today: string): string {
  const [y, m] = today.split("-").map(Number);
  const d = new Date(Date.UTC(y, m - 2, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

const MONTH = /^(19|20)\d{2}-(0[1-9]|1[0-2])$/;

/** HR: Monthly report (R28). Pick a month, download Excel or CSV. The file is confidential. */
export function MonthlyReportPage() {
  const [month, setMonth] = useState(previousMonth(todayIso()));
  const valid = MONTH.test(month);
  const href = (format: "xlsx" | "csv") => `/api/v1/hr/reports/monthly?month=${month}&format=${format}`;
  return (
    <section aria-labelledby="report-title">
      <h1 id="report-title">Monthly report</h1>
      <p>
        Days taken per person and type, remaining balances at the end of the month, and who was off and when. Approved
        leave only. Every export is recorded.
      </p>
      <Field
        label="Month"
        hint="Choose the month, for example 2026-10."
        error={valid ? undefined : "Enter a month as YYYY-MM, for example 2026-10."}
      >
        {(c) => <input className="input" type="month" value={month} onChange={(e) => setMonth(e.target.value)} {...c} />}
      </Field>
      {valid ? (
        <p>
          <a className="btn btn--primary" href={href("xlsx")} download>
            Export Excel
          </a>{" "}
          <a className="btn btn--secondary" href={href("csv")} download>
            Export CSV
          </a>
        </p>
      ) : null}
      <p role="note">
        Confidential: the file shows Sick leave types. Keep it with HR and do not forward it.
      </p>
    </section>
  );
}
