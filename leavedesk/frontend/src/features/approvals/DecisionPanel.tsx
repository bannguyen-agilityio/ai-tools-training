import { useState } from "react";
import { ApiError } from "../../api/problem";
import { Button } from "../../ui/Button";
import type { LeaveRequest } from "../requests/api";
import { useDecide } from "./api";
import { RejectForm } from "./RejectForm";

function message(error: unknown): string | undefined {
  if (!error) return undefined;
  return error instanceof ApiError
    ? error.message
    : "Could not save the decision. Try again.";
}

/** Approve or reject one Pending request. A stale version shows the server's 409 message. */
export function DecisionPanel({
  request,
  onBehalfOf,
}: {
  request: LeaveRequest;
  onBehalfOf?: string;
}) {
  const [rejecting, setRejecting] = useState(false);
  const approve = useDecide(request.id, "approve");
  const reject = useDecide(request.id, "reject");
  const failure = message(approve.error ?? reject.error);
  const reasonError =
    reject.error instanceof ApiError && reject.error.status === 422
      ? reject.error.message
      : undefined;

  if (approve.isSuccess || reject.isSuccess) {
    return (
      <p role="status">
        {approve.isSuccess ? "Request approved." : "Request rejected."}
      </p>
    );
  }
  return (
    <section aria-label="Decision">
      {failure && !reasonError && <p role="alert">{failure}</p>}
      {rejecting ? (
        <RejectForm
          pending={reject.isPending}
          serverError={reasonError}
          onSubmit={(reason) =>
            reject.mutate({
              version: request.version,
              reason,
              on_behalf_of: onBehalfOf,
            })
          }
          onCancel={() => setRejecting(false)}
        />
      ) : (
        <>
          <Button
            disabled={approve.isPending}
            onClick={() => approve.mutate({
                version: request.version,
                on_behalf_of: onBehalfOf,
              })}
          >
            Approve
          </Button>{" "}
          <Button variant="danger" onClick={() => setRejecting(true)}>
            Reject
          </Button>
        </>
      )}
    </section>
  );
}
