import { formatDate, todayIso } from "../../../lib/dates";
import { Button } from "../../../ui/Button";
import { BalanceList } from "./BalanceList";
import type { BalanceRow } from "./api";

/** The "balances at launch" list staff check and sign off in week 1 (C-9). Print stylesheet hides
 * everything else (`.print-only` / `.no-print` in app.css). */
export function PrintView({ year, rows }: { year: number; rows: BalanceRow[] }) {
  return (
    <section aria-labelledby="launch-title">
      <h2 id="launch-title">Balances at launch {year}</h2>
      <p className="print-only">
        Printed {formatDate(todayIso())}. Tick your row if correct; report mistakes to HR in week 1.
      </p>
      <p className="no-print">
        <Button variant="secondary" onClick={() => window.print()}>
          Print this list
        </Button>
      </p>
      <BalanceList rows={rows} checkColumn />
    </section>
  );
}
