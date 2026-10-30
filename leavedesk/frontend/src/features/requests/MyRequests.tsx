import { Link } from "react-router-dom";
import { useMyRequests } from "./api";
import { daysText, rangeText, statusText, typeLabel } from "./format";

export function MyRequests() {
  const { data, isPending, isError } = useMyRequests();
  return (
    <section aria-labelledby="my-requests-title">
      <h1 id="my-requests-title">My requests</h1>
      <Link to="/requests/new" className="btn btn--primary">
        Request leave
      </Link>
      {isPending && <p>Loading your requests…</p>}
      {isError && (
        <p role="alert">Could not load your requests. Try again later.</p>
      )}
      {data && data.length === 0 && (
        <p>You have not requested any leave yet.</p>
      )}
      {data && data.length > 0 && (
        <table>
          <caption className="visually-hidden">
            Your leave requests, newest first
          </caption>
          <thead>
            <tr>
              <th scope="col">Dates</th>
              <th scope="col">Type</th>
              <th scope="col">Days</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.id}>
                <th scope="row">
                  <Link to={`/requests/${r.id}`}>{rangeText(r)}</Link>
                </th>
                <td>{typeLabel(r)}</td>
                <td>{daysText(r.working_days)}</td>
                <td>{statusText(r.status)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
