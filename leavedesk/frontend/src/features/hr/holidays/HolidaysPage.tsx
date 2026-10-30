import { useState } from "react";
import { ApiError } from "../../../api/problem";
import { formatDate, todayIso } from "../../../lib/dates";
import { Button } from "../../../ui/Button";
import { ConfirmDialog } from "../../../ui/ConfirmDialog";
import { useToast } from "../../../ui/Toast";
import { useHolidayMutations, useHolidays, useImpact, type Holiday } from "./api";
import { HolidayForm } from "./HolidayForm";

type Mode = { kind: "list" } | { kind: "add" } | { kind: "edit"; holiday: Holiday };

function requestsText(n: number): string {
  return `${n} ${n === 1 ? "request" : "requests"} affected`;
}

/** The impact count for one row's delete confirmation. */
function DeleteConfirm({ holiday, onConfirm, onKeep }: { holiday: Holiday; onConfirm: () => void; onKeep: () => void }) {
  const impact = useImpact(holiday.holiday_date);
  const count = impact.data;
  const when = formatDate(holiday.holiday_date);
  return (
    <ConfirmDialog
      open
      title="Delete this holiday?"
      consequence={
        count === undefined
          ? `Removes ${holiday.name} on ${when}. ${impact.isError ? "The number of affected requests could not be counted." : "Counting affected requests..."}`
          : `Removes ${holiday.name} on ${when}. ${requestsText(count)}: their saved day counts do not change, so HR adjusts them through the ledger.`
      }
      confirmLabel="Delete holiday"
      keepLabel="Keep"
      onConfirm={onConfirm}
      onKeep={onKeep}
    />
  );
}

export function HolidaysPage() {
  const [year, setYear] = useState(() => Number(todayIso().slice(0, 4)));
  const [mode, setMode] = useState<Mode>({ kind: "list" });
  const [deleting, setDeleting] = useState<Holiday | null>(null);
  const [serverError, setServerError] = useState<string>();
  const holidays = useHolidays(year);
  const { create, update, remove } = useHolidayMutations();
  const toast = useToast();

  const fail = (e: unknown) => setServerError(e instanceof ApiError ? e.message : "Could not save the holiday.");
  const saved = (verb: string, affected: number) => {
    toast("success", `Holiday ${verb}. ${requestsText(affected)}.`);
    setMode({ kind: "list" });
    setServerError(undefined);
  };

  if (mode.kind !== "list") {
    const editing = mode.kind === "edit" ? mode.holiday : undefined;
    return (
      <HolidayForm
        initial={editing && { holiday_date: editing.holiday_date, name: editing.name }}
        serverError={serverError}
        busy={create.isPending || update.isPending}
        onCancel={() => {
          setMode({ kind: "list" });
          setServerError(undefined);
        }}
        onSubmit={(values) =>
          editing
            ? update.mutate({ id: editing.id, body: values }, { onSuccess: (r) => saved("updated", r.affected_requests), onError: fail })
            : create.mutate(values, { onSuccess: (r) => saved("added", r.affected_requests), onError: fail })
        }
      />
    );
  }

  return (
    <section aria-labelledby="holidays-title">
      <h1 id="holidays-title">Public holidays {year}</h1>
      <p>
        <Button variant="secondary" onClick={() => setYear(year - 1)}>
          Previous year
        </Button>{" "}
        <Button variant="secondary" onClick={() => setYear(year + 1)}>
          Next year
        </Button>{" "}
        <Button onClick={() => setMode({ kind: "add" })}>Add holiday</Button>
      </p>
      {holidays.isError && <p role="alert">Could not load holidays.</p>}
      {holidays.data && holidays.data.length === 0 && <p>No holidays are set for {year}.</p>}
      {holidays.data && holidays.data.length > 0 && (
        <table>
          <caption className="visually-hidden">Public holidays in {year}</caption>
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Name</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {holidays.data.map((h) => (
              <tr key={h.id}>
                <th scope="row">{formatDate(h.holiday_date)}</th>
                <td>{h.name}</td>
                <td>
                  <Button
                    variant="secondary"
                    aria-label={`Edit ${h.name} on ${formatDate(h.holiday_date)}`}
                    onClick={() => setMode({ kind: "edit", holiday: h })}
                  >
                    Edit
                  </Button>{" "}
                  <Button
                    variant="danger"
                    aria-label={`Delete ${h.name} on ${formatDate(h.holiday_date)}`}
                    onClick={() => setDeleting(h)}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {deleting && (
        <DeleteConfirm
          holiday={deleting}
          onKeep={() => setDeleting(null)}
          onConfirm={() =>
            remove.mutate(deleting.id, {
              onSuccess: (r) => {
                toast("success", `Holiday deleted. ${requestsText(r.affected_requests)}.`);
                setDeleting(null);
              },
              onError: (e) => {
                toast("error", e instanceof ApiError ? e.message : "Could not delete the holiday.");
                setDeleting(null);
              },
            })
          }
        />
      )}
    </section>
  );
}
