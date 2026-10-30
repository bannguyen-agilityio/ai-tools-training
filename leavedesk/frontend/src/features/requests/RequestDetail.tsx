import { Link, useParams } from "react-router-dom";
import { ApiError } from "../../api/problem";
import { useRequest } from "./api";
import { daysText, rangeText, statusText, typeLabel } from "./format";

export function RequestDetail() {
  const { id = "" } = useParams();
  const { data, isPending, error } = useRequest(id);
  if (isPending) return <p>Loading the request…</p>;
  if (error || !data) {
    const denied =
      error instanceof ApiError &&
      (error.status === 403 || error.status === 404);
    return (
      <p role="alert">
        {denied
          ? "You cannot view this request."
          : "Could not load the request."}
      </p>
    );
  }
  return (
    <section aria-labelledby="request-title">
      <h1 id="request-title">Leave request</h1>
      {data.notice_warning && (
        <p role="status">
          Short notice: this long request starts within a week.
        </p>
      )}
      <dl>
        <dt>Dates</dt>
        <dd>{rangeText(data)}</dd>
        <dt>Type</dt>
        <dd>{typeLabel(data)}</dd>
        <dt>Working days</dt>
        <dd>{daysText(data.working_days)}</dd>
        <dt>Status</dt>
        <dd>{statusText(data.status)}</dd>
        {data.note && (
          <>
            <dt>Note</dt>
            <dd>{data.note}</dd>
          </>
        )}
      </dl>
      <Link to="/requests">Back to my requests</Link>
    </section>
  );
}
