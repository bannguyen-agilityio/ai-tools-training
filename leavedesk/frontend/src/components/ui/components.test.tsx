import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { formatDays, formatQuantity } from "../../lib/days";
import { Alert, EmptyState } from "./Feedback";
import { ConfirmDialog } from "./ConfirmDialog";
import { DaysText } from "./DateText";
import { LeaveTypeTag } from "./LeaveTypeTag";
import { StatusBadge, type Status } from "./StatusBadge";

describe("StatusBadge", () => {
  it.each(["pending", "approved", "rejected", "cancelled"] as Status[])("shows a text label for %s", (s) => {
    const { container } = render(<StatusBadge status={s} />);
    expect(container.textContent).toMatch(new RegExp(s, "i"));
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeNull();
  });
  it("tells Pending from Approved by label", () => {
    const { container: a } = render(<StatusBadge status="pending" />);
    const { container: b } = render(<StatusBadge status="approved" />);
    expect(a.textContent).not.toBe(b.textContent);
  });
});

describe("LeaveTypeTag", () => {
  it("renders Off when the API sent no type, and never guesses", () => {
    const { container } = render(<LeaveTypeTag type={null} />);
    expect(container).toHaveTextContent("Off");
    expect(container.innerHTML).not.toMatch(/sick/i);
  });
  it("uses the neutral style for Sick, with no sick class", () => {
    const { container } = render(<LeaveTypeTag type="sick" />);
    expect(container.innerHTML).not.toMatch(/tag--sick/);
  });
  it("shows the given type", () => {
    render(<LeaveTypeTag type="annual" />);
    expect(screen.getByText("Annual")).toBeInTheDocument();
  });
});

describe("days formatting", () => {
  it.each([
    [0.5, "½ day"],
    [1, "1 day"],
    [8, "8 days"],
    [8.5, "8½ days"],
    [0.30000000000000004 + 0.2, "½ day"],
  ])("%s -> %s", (n, text) => expect(formatDays(n)).toBe(text));
  it("quantity has no unit", () => expect(formatQuantity(8.5)).toBe("8½"));
  it("DaysText renders it", () => {
    render(<DaysText value={2.5} />);
    expect(screen.getByText("2½ days")).toBeInTheDocument();
  });
});

describe("ConfirmDialog", () => {
  it("focuses Keep and keeps on Escape", async () => {
    const onKeep = vi.fn();
    render(<ConfirmDialog open title="Cancel request" consequence="Cancels it." confirmLabel="Cancel request" onConfirm={vi.fn()} onKeep={onKeep} />);
    expect(screen.getByRole("button", { name: "Keep" })).toHaveFocus();
    await userEvent.keyboard("{Escape}");
    expect(onKeep).toHaveBeenCalled();
  });
});

describe("Feedback", () => {
  it("announces errors with a retry", async () => {
    const onRetry = vi.fn();
    render(<Alert tone="danger" onRetry={onRetry}>Could not load.</Alert>);
    expect(screen.getByRole("alert")).toHaveTextContent("Error: Could not load.");
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalled();
  });
  it("renders an empty state", () => {
    render(<EmptyState title="No upcoming leave" />);
    expect(screen.getByText("No upcoming leave")).toBeInTheDocument();
  });
});
