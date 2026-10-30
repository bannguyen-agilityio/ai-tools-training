import { useState } from "react";
import { ApiError } from "../../../api/problem";
import { Button } from "../../../ui/Button";
import { useToast } from "../../../ui/Toast";
import { useBalanceList, useEmployeeBalances, useEntryMutations, type BalanceRow, type EntryInput } from "./api";
import { BalanceList } from "./BalanceList";
import { ConfirmSummary } from "./ConfirmSummary";
import { EntryForm } from "./EntryForm";
import { PrintView } from "./PrintView";

type Step = { kind: "list" } | { kind: "print" } | { kind: "form" } | { kind: "confirm"; entry: EntryInput };

const message = (e: unknown) => (e instanceof ApiError ? e.message : "Could not save the entry.");

export function BalancesPage() {
  const [step, setStep] = useState<Step>({ kind: "list" });
  const [employee, setEmployee] = useState<BalanceRow>();
  const [serverError, setServerError] = useState<string>();
  const list = useBalanceList();
  const toast = useToast();

  const back = () => {
    setStep({ kind: "list" });
    setEmployee(undefined);
    setServerError(undefined);
  };

  if (step.kind === "print" && list.data) {
    return (
      <>
        <p className="no-print">
          <Button variant="secondary" onClick={back}>
            Back to balances
          </Button>
        </p>
        <PrintView year={list.data.leave_year} rows={list.data.items} />
      </>
    );
  }
  if (employee && step.kind !== "list" && step.kind !== "print") {
    return (
      <EntryFlow
        employee={employee}
        step={step}
        setStep={setStep}
        serverError={serverError}
        setServerError={setServerError}
        onDone={() => {
          toast("success", `Entry saved for ${employee.employee_name}.`);
          back();
        }}
        onCancel={back}
      />
    );
  }

  return (
    <section aria-labelledby="balances-title">
      <h1 id="balances-title">Starting balances</h1>
      <p>
        <Button variant="secondary" onClick={() => setStep({ kind: "print" })} disabled={!list.data}>
          Balances at launch (printable)
        </Button>
      </p>
      {list.isError && <p role="alert">Could not load balances.</p>}
      {list.data && (
        <BalanceList
          rows={list.data.items}
          onSelect={(row) => {
            setEmployee(row);
            setStep({ kind: "form" });
          }}
        />
      )}
    </section>
  );
}

interface FlowProps {
  employee: BalanceRow;
  step: Step;
  setStep: (s: Step) => void;
  serverError?: string;
  setServerError: (m?: string) => void;
  onDone: () => void;
  onCancel: () => void;
}

function EntryFlow({ employee, step, setStep, serverError, setServerError, onDone, onCancel }: FlowProps) {
  const { preview, save } = useEntryMutations(employee.employee_id);
  const ledger = useEmployeeBalances(employee.employee_id);
  const [summary, setSummary] = useState<Awaited<ReturnType<typeof preview.mutateAsync>>>();

  if (step.kind === "confirm" && summary) {
    return (
      <ConfirmSummary
        summary={summary}
        busy={save.isPending}
        serverError={serverError}
        onBack={() => setStep({ kind: "form" })}
        onSave={() => save.mutate(step.entry, { onSuccess: onDone, onError: (e) => setServerError(message(e)) })}
      />
    );
  }
  return (
    <>
      <EntryForm
        employeeName={employee.employee_name}
        serverError={serverError}
        busy={preview.isPending}
        onCancel={onCancel}
        onSubmit={(entry) => {
          setServerError(undefined);
          preview.mutate(entry, {
            onSuccess: (s) => {
              setSummary(s);
              setStep({ kind: "confirm", entry });
            },
            onError: (e) => setServerError(message(e)),
          });
        }}
      />
      {ledger.data && (
        <section aria-labelledby="ledger-title">
          <h2 id="ledger-title">Ledger {ledger.data.leave_year}, newest first</h2>
          {ledger.data.ledger.length === 0 ? (
            <p>No entries yet.</p>
          ) : (
            <table>
              <caption className="visually-hidden">Ledger entries</caption>
              <thead>
                <tr>
                  <th scope="col">Type</th>
                  <th scope="col">Entry</th>
                  <th scope="col">Days</th>
                  <th scope="col">Reason</th>
                </tr>
              </thead>
              <tbody>
                {ledger.data.ledger.map((e) => (
                  <tr key={e.id}>
                    <td>{e.leave_type_code === "sick" ? "Sick" : "Annual"}</td>
                    <td>{e.kind.replace("_", " ")}</td>
                    <td>{e.days}</td>
                    <td>{e.reason ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </>
  );
}
