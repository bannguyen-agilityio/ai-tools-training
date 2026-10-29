import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { axe } from "vitest-axe";
import { SampleForm } from "../SampleForm";
import { ConfirmDialog } from "./ConfirmDialog";
import { DateField } from "./DateField";
import { Field } from "./Field";
import { TextField } from "./TextField";

describe("Field (R31b)", () => {
  it("links label, hint and error to the control", () => {
    render(<TextField label="Name" hint="As on your badge" error="Enter a name" />);
    const input = screen.getByLabelText("Name");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription(/As on your badge/);
    expect(input).toHaveAccessibleDescription(/Enter a name/);
  });
  it("has no aria-invalid without an error", () => {
    render(<Field label="X">{(c) => <input {...c} />}</Field>);
    expect(screen.getByLabelText("X")).not.toHaveAttribute("aria-invalid");
  });
});

describe("SampleForm (R31b, R31d)", () => {
  it("keeps input, summarises errors and focuses the first invalid field", async () => {
    const user = userEvent.setup();
    render(<SampleForm />);
    await user.type(screen.getByLabelText("Your name"), "Linh");
    await user.clear(screen.getByLabelText("Your name"));
    await user.click(screen.getByRole("button", { name: "Submit request" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("2 things need fixing");
    expect(screen.getByLabelText("Your name")).toHaveFocus();
  });
  it("retains values on invalid submit", async () => {
    const user = userEvent.setup();
    render(<SampleForm />);
    await user.type(screen.getByLabelText("Your name"), "Linh");
    await user.click(screen.getByRole("button", { name: "Submit request" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("1 thing needs fixing");
    expect(screen.getByLabelText("Your name")).toHaveValue("Linh");
    expect(screen.getByLabelText("First day")).toHaveFocus();
  });
  it("has no axe violations", async () => {
    const { container } = render(<SampleForm />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("ConfirmDialog (R31e)", () => {
  function setup() {
    const onKeep = vi.fn();
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        title="Cancel request?"
        consequence="Cancels Mon 2 Nov 2026 (1 day)."
        confirmLabel="Cancel request"
        onKeep={onKeep}
        onConfirm={onConfirm}
      />,
    );
    return { onKeep, onConfirm };
  }
  it("opens with focus on Keep", () => {
    setup();
    expect(screen.getByRole("button", { name: "Keep" })).toHaveFocus();
  });
  it("Escape keeps", async () => {
    const { onKeep, onConfirm } = setup();
    await userEvent.keyboard("{Escape}");
    expect(onKeep).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });
  it("traps Tab inside", async () => {
    setup();
    await userEvent.tab();
    expect(screen.getByRole("button", { name: "Cancel request" })).toHaveFocus();
    await userEvent.tab();
    expect(screen.getByRole("button", { name: "Keep" })).toHaveFocus();
  });
  it("has no axe violations", async () => {
    setup();
    expect(await axe(document.body)).toHaveNoViolations();
  });
});

describe("DateField (R31c)", () => {
  function Harness() {
    const [iso, setIso] = useState("2026-11-02");
    return (
      <>
        <DateField label="Day" value={iso} onChange={setIso} />
        <output>{iso || "none"}</output>
      </>
    );
  }
  it("shows the unambiguous format and round-trips to ISO", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const input = screen.getByLabelText("Day");
    expect(input).toHaveValue("Mon 2 Nov 2026");
    await user.clear(input);
    await user.type(input, "3 Nov 2026");
    expect(screen.getByRole("status")).toHaveTextContent("2026-11-03");
    await user.tab();
    expect(input).toHaveValue("Tue 3 Nov 2026");
  });
  it("explains an unreadable date", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.clear(screen.getByLabelText("Day"));
    await user.type(screen.getByLabelText("Day"), "11/02/2026");
    expect(screen.getByLabelText("Day")).toHaveAccessibleDescription(/Not a date/);
  });
});
