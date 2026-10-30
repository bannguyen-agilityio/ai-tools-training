import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../../api/problem";
import { useMe } from "../../auth/useMe";
import { Button } from "../../ui/Button";
import { ConfirmDialog } from "../../ui/ConfirmDialog";
import { useToast } from "../../ui/Toast";
import { useCancelRequest, useRequest } from "./api";
import { daysText, rangeText, statusText, typeLabel } from "./format";

export function RequestDetail() {
  const { id = "" } = useParams();
  const { data, isPending, error, refetch } = useRequest(id);
  const { data: me } = useMe();
  const cancel = useCancelRequest(id);
  const toast = useToast();
  const [confirming, setConfirming] = useState(false);
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
  // R16: only the owner, only while Pending. The server enforces it too (403).
  const canCancel = data.status === "pending" && me?.id === data.employee_id;
  const { version } = data;
  function confirmCancel() {
    setConfirming(false);
    cancel.mutate(version, {
      onSuccess: () =>
        toast("success", "Request cancelled. The days are released."),
      // Stale version or no longer Pending: show the server's current state, not the old one.
      onError: () => void refetch(),
    });
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
      {cancel.error && <p role="alert">{cancel.error.message}</p>}
      {canCancel && (
        <Button
          variant="danger"
          onClick={() => {
            cancel.reset();
            setConfirming(true);
          }}
          disabled={cancel.isPending}
        >
          Cancel request
        </Button>
      )}
      <ConfirmDialog
        open={confirming}
        title="Cancel this request?"
        consequence={`Cancels your request for ${rangeText(data)} (${daysText(data.working_days)}).`}
        confirmLabel="Cancel request"
        onConfirm={confirmCancel}
        onKeep={() => setConfirming(false)}
      />
      <Link to="/requests">Back to my requests</Link>
    </section>
  );
}
