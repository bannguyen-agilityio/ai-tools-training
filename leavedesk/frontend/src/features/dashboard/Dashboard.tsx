import { Link } from "react-router-dom";
import { useMyBalances } from "./api";
import { BalanceCard } from "./BalanceCard";

export function Dashboard() {
  const { data, isPending, isError } = useMyBalances();
  return (
    <>
      <h1>LeaveDesk</h1>
      <Link to="/requests/new" className="btn btn--primary">
        Request leave
      </Link>
      {isPending && <p>Loading your balances…</p>}
      {isError && <p role="alert">Could not load your balances. Try again later.</p>}
      {data && (
        <>
          <h2>Balances for {data.year}</h2>
          {data.balances.map((b) => (
            <BalanceCard key={b.leave_type} balance={b} />
          ))}
        </>
      )}
      <section aria-labelledby="upcoming">
        <h2 id="upcoming">Upcoming leave</h2>
        <p>Your upcoming leave will appear here.</p>
      </section>
    </>
  );
}
