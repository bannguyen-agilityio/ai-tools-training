import { formatDate } from "../../lib/dates";
import type { TypeBalance } from "./api";

const TITLES = { annual: "Annual leave", sick: "Sick leave" } as const;

export function BalanceCard({ balance }: { balance: TypeBalance }) {
  const title = TITLES[balance.leave_type];
  const rows: [string, string][] = [
    ["Entitlement", `${balance.entitlement} days`],
    ["Used (Approved)", `${balance.used} days`],
    ["Reserved (Pending)", `${balance.reserved} days`],
  ];
  if (balance.carried > 0 && balance.expires_on) {
    rows.splice(1, 0, [
      "Carried over",
      `${balance.carried} days, ${balance.carried_expired ? "expired" : "expire"} ${formatDate(balance.expires_on)}`,
    ]);
  }
  return (
    <section aria-labelledby={`bal-${balance.leave_type}`} className="card">
      <h2 id={`bal-${balance.leave_type}`}>{title}</h2>
      <p>
        <strong>{balance.available} days available</strong>
      </p>
      <dl>
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
