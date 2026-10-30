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
  // One mutation, so a later outcome always replaces an earlier error.
  const decide = useDecide(request.id);
  const failure = message(decide.error);
  const reasonError =
    decide.error instanceof ApiError &&
    decide.error.status === 422 &&
    decide.variables?.action === "reject"
      ? decide.error.message
      : undefined;

  if (decide.isSuccess) {
    return (
      <p role="status">
        {decide.variables.action === "approve"
          ? "Request approved."
          : "Request rejected."}
      </p>
    );
  }
  return (
    <section aria-label="Decision">
      {failure && !reasonError && <p role="alert">{failure}</p>}
      {rejecting ? (
        <RejectForm
          pending={decide.isPending}
          serverError={reasonError}
          onSubmit={(reason) =>
            decide.mutate({
              action: "reject",
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
            disabled={decide.isPending}
            onClick={() =>
              decide.mutate({
                action: "approve",
                version: request.version,
                on_behalf_of: onBehalfOf,
              })
            }
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
