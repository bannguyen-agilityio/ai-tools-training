import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../../api/problem";
import { Button } from "../../ui/Button";
import { DateField } from "../../ui/DateField";
import { ErrorSummary, type SummaryItem } from "../../ui/ErrorSummary";
import { Select } from "../../ui/Select";
import { TextField } from "../../ui/TextField";
import {
  useCreateRequest,
  usePreview,
  type LeaveType,
  type Part,
  type RequestInput,
} from "./api";
import { daysText } from "./format";

const TYPES = [
  { value: "annual", label: "Annual" },
  { value: "sick", label: "Sick" },
  { value: "unpaid", label: "Unpaid" },
];
const FIRST = [
  { value: "full", label: "Full day" },
  { value: "pm", label: "Afternoon only" },
];
const LAST = [
  { value: "full", label: "Full day" },
  { value: "am", label: "Morning only" },
];
const SINGLE = [
  { value: "full", label: "Full day" },
  { value: "am", label: "Morning" },
  { value: "pm", label: "Afternoon" },
];
const FIELD_NAMES = new Set([
  "leave_type",
  "start_date",
  "start_part",
  "end_date",
  "end_part",
  "note",
]);

export function NewRequest() {
  const [type, setType] = useState<LeaveType>("annual");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [startPart, setStartPart] = useState<Part>("full");
  const [endPart, setEndPart] = useState<Part>("full");
  const [note, setNote] = useState("");
  const [submitError, setSubmitError] = useState<ApiError>();
  const create = useCreateRequest();
  const navigate = useNavigate();

  const single = start !== "" && (end === "" || end === start);
  const effectiveEnd = end || start;
  // A single day takes one part for both ends (Q7); otherwise first and last day pick their own.
  const input: RequestInput | null =
    start && effectiveEnd
      ? {
          leave_type: type,
          start_date: start,
          end_date: effectiveEnd,
          start_part: startPart,
          end_part: single ? startPart : endPart,
          ...(note.trim() ? { note: note.trim() } : {}),
        }
      : null;
  const preview = usePreview(input);

  const fieldMessage = (name: string): string | undefined => {
    const hit = preview.data?.errors.find((e) => e.field === name);
    return (
      hit?.message ?? submitError?.fields.find((f) => f.field === name)?.message
    );
  };

  const summary: SummaryItem[] = [
    ...(preview.data?.errors ?? []).map((e) => ({
      fieldName: e.field && FIELD_NAMES.has(e.field) ? e.field : undefined,
      message: e.message,
    })),
    ...(submitError &&
    !preview.data?.errors.some((e) => e.message === submitError.message)
      ? [{ message: submitError.message }]
      : []),
  ];

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input) {
      setSubmitError(new ApiError(422, "Choose a start date."));
      return;
    }
    setSubmitError(undefined);
    create.mutate(input, {
      onSuccess: (r) => navigate(`/requests/${r.id}`),
      onError: (err) => {
        setSubmitError(
          err instanceof ApiError
            ? err
            : new ApiError(500, "Could not submit the request."),
        );
        document.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
      },
    });
  };

  const year = preview.data?.per_year;
  return (
    <section aria-labelledby="new-request-title">
      <h1 id="new-request-title">Request leave</h1>
      <ErrorSummary items={summary} />
      <form onSubmit={onSubmit} noValidate>
        <Select
          label="Leave type"
          name="leave_type"
          value={type}
          options={TYPES}
          onChange={(e) => setType(e.target.value as LeaveType)}
        />
        <DateField
          label="Start date"
          name="start_date"
          value={start}
          onChange={setStart}
          error={fieldMessage("start_date")}
        />
        <DateField
          label="End date"
          name="end_date"
          value={end}
          onChange={setEnd}
          error={fieldMessage("end_date")}
        />
        {single ? (
          <Select
            label="Which part of the day"
            name="start_part"
            value={startPart}
            options={SINGLE}
            onChange={(e) => setStartPart(e.target.value as Part)}
          />
        ) : (
          <>
            <Select
              label="First day"
              name="start_part"
              value={startPart}
              options={FIRST}
              onChange={(e) => setStartPart(e.target.value as Part)}
              error={fieldMessage("start_part")}
            />
            <Select
              label="Last day"
              name="end_part"
              value={endPart}
              options={LAST}
              onChange={(e) => setEndPart(e.target.value as Part)}
              error={fieldMessage("end_part")}
            />
          </>
        )}
        <TextField
          label="Note (optional)"
          name="note"
          maxLength={500}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          hint="Only you, your approver and HR can read it."
        />
        <p aria-live="polite">
          {preview.data?.working_days != null && (
            <strong>{daysText(preview.data.working_days)}</strong>
          )}
          {year?.map((y) =>
            y.available_after === null ? null : (
              <span key={y.year}>
                {" "}
                {year.length > 1 ? `${y.year}: ` : ""}
                {y.available_after} left after this request.
              </span>
            ),
          )}
        </p>
        <Button type="submit" disabled={create.isPending}>
          Submit request
        </Button>
      </form>
    </section>
  );
}
