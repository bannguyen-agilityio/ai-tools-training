import { Alert, Skeleton } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Card";
import { DaysText } from "../../components/ui/DateText";
import { formatDate, todayIso } from "../../lib/dates";
import { formatQuantity } from "../../lib/days";
import type { TypeBalance } from "./api";
import { annualTotal, expiresSoon } from "./summary";

/** Segmented bar. aria-hidden: the caption below says the same in words. SVG attributes, not style (CSP). */
function Bar({ b }: { b: TypeBalance }) {
  const total = annualTotal(b) || 1;
  const used = Math.min(100, (b.used / total) * 100);
  const reserved = Math.min(100 - used, (b.reserved / total) * 100);
  return (
    <svg className="bar" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <rect className="bar__track" x="0" y="0" width="100" height="8" />
      <rect className="bar__used" x="0" y="0" width={used} height="8" />
      <rect className="bar__reserved" x={used} y="0" width={reserved} height="8" />
    </svg>
  );
}

export function AnnualCard({ b }: { b: TypeBalance }) {
  const today = todayIso();
  const carried = b.carried > 0 && !b.carried_expired;
  const soon = expiresSoon(b, today);
  return (
    <Card className="balance balance--hero">
      <h2>Annual leave available</h2>
      <p className="figure">
        <span className="figure__value num">{formatQuantity(b.available)}</span>
        <span className="figure__of"> of {formatQuantity(annualTotal(b))} days</span>
      </p>
      <Bar b={b} />
      <p className="caption">
        {formatQuantity(b.used)} used · {formatQuantity(b.reserved)} reserved
        {carried && (
          <>
            {" · "}
            <span className={soon ? "text-warning" : undefined}>
              {formatQuantity(b.carried)} carried, expire {formatDate(b.expires_on!)}
              {soon && <span className="visually-hidden"> (expires soon)</span>}
            </span>
          </>
        )}
      </p>
    </Card>
  );
}

export function SickCard({ b }: { b: TypeBalance }) {
  return (
    <Card className="balance">
      <h2>Sick leave available</h2>
      <p className="figure">
        <span className="figure__value num">{formatQuantity(b.available)}</span>
      </p>
      <p className="caption">
        {formatQuantity(b.used)} of {formatQuantity(b.entitlement)} used
      </p>
    </Card>
  );
}

/** Unpaid has no balance (R5, R10): never a number, only days taken. */
export function UnpaidCard({ taken }: { taken: number | null }) {
  return (
    <Card className="balance">
      <h2>Unpaid leave</h2>
      <p className="figure">
        <span className="figure__value" aria-label="No balance">
          —
        </span>
      </p>
      <p className="caption">
        No limit{taken !== null && <> · <DaysText value={taken} /> taken</>}
      </p>
    </Card>
  );
}

export function BalanceSkeleton({ hero = false }: { hero?: boolean }) {
  return (
    <Card className={hero ? "balance balance--hero" : "balance"}>
      <Skeleton className="skeleton--line" />
      <Skeleton className="skeleton--figure" />
      <Skeleton className="skeleton--line" />
    </Card>
  );
}

export function BalanceError({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className="balance balance--hero">
      <Alert tone="danger" onRetry={onRetry}>
        Could not load your balances.
      </Alert>
    </Card>
  );
}

