import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { axe } from "vitest-axe";
import { AllLeavePage } from "./AllLeavePage";

const ROW = {
  id: "r1",
  employee_id: "e",
  employee_name: "Eli Employee",
  team_id: null,
  leave_type: "sick",
  start_date: "2026-11-02",
  start_part: "full",
  end_date: "2026-11-04",
  end_part: "full",
  working_days: 3,
  note: "flu",
  status: "approved",
  version: 1,
};

function json(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
}

function mockApi(urls: string[] = [], items: unknown[] = [ROW]) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    urls.push(url);
    if (url.includes("/hr/leave")) return json({ items, next_cursor: null });
    return json({ items: [], next_cursor: null });
  });
  return urls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <AllLeavePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("AllLeavePage (R25)", () => {
  it("lists approved leave with the real type and an unambiguous date, no axe violations", async () => {
    const urls = mockApi();
    const { container } = renderPage();
    expect(await screen.findByText("Eli Employee")).toBeInTheDocument();
    const row = screen.getByRole("row", { name: /Eli Employee/ });
    expect(within(row).getByText("Sick")).toBeInTheDocument();
    expect(screen.getByText("Mon 2 Nov 2026 to Wed 4 Nov 2026")).toBeInTheDocument();
    expect(urls.find((u) => u.includes("/hr/leave"))).toContain("status=approved");
    expect(await axe(container)).toHaveNoViolations();
  });

  it("sends the chosen filters and says when nothing matches", async () => {
    const user = userEvent.setup();
    const urls = mockApi([], []);
    renderPage();
    expect(await screen.findByText("No leave matches these filters.")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Status"), "pending");
    await user.selectOptions(screen.getByLabelText("Type"), "sick");
    await vi.waitFor(() => {
      const last = urls.filter((u) => u.includes("/hr/leave")).pop() ?? "";
      expect(last).toContain("status=pending");
      expect(last).toContain("type=sick");
    });
  });

  it("flags a range that ends before it starts", async () => {
    const user = userEvent.setup();
    mockApi();
    renderPage();
    await screen.findByText("Eli Employee");
    await user.type(screen.getByLabelText("From"), "2026-11-10");
    await user.type(screen.getByLabelText("To"), "2026-11-01");
    expect(await screen.findByText("The end is before the start.")).toBeInTheDocument();
  });
});
