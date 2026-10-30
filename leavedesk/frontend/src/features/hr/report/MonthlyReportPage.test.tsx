import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { MonthlyReportPage } from "./MonthlyReportPage";

describe("MonthlyReportPage (R28)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-16T05:00:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("defaults to last month and offers both formats in two clicks or fewer", async () => {
    const { container } = render(<MonthlyReportPage />);
    expect(screen.getByLabelText("Month")).toHaveValue("2026-10");
    expect(screen.getByRole("link", { name: "Export Excel" })).toHaveAttribute(
      "href",
      "/api/v1/hr/reports/monthly?month=2026-10&format=xlsx",
    );
    expect(screen.getByRole("link", { name: "Export CSV" })).toHaveAttribute(
      "href",
      "/api/v1/hr/reports/monthly?month=2026-10&format=csv",
    );
    expect(screen.getByRole("note")).toHaveTextContent("Confidential");
    expect(await axe(container)).toHaveNoViolations();
  });

  it("withdraws the download links and explains when the month is not valid", async () => {
    const user = userEvent.setup({ delay: null });
    render(<MonthlyReportPage />);
    await user.clear(screen.getByLabelText("Month"));
    expect(screen.getByText(/Enter a month as YYYY-MM/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Export Excel" })).toBeNull();
  });
});
