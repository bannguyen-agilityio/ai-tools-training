import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { ToastProvider } from "../../../ui/Toast";
import { EmployeesPage } from "./EmployeesPage";

const EMPLOYEES = [
  { id: "m", name: "Mai Manager", email: "mai@asnet.com.vn", role: "manager", is_hr_deputy: false, team_id: "t", manager_id: null, start_date: "2024-03-04", is_active: true },
  { id: "e", name: "Eli Employee", email: "eli@asnet.com.vn", role: "employee", is_hr_deputy: false, team_id: "t", manager_id: "m", start_date: "2026-07-01", is_active: true },
];
const TEAMS = [{ id: "t", name: "Platform", manager_id: "m" }];

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockApi(calls: { method: string; url: string; body?: string }[] = []) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    calls.push({ method, url, body: init?.body as string | undefined });
    if (method === "POST" && url.endsWith("/invite")) return new Response(null, { status: 204 });
    if (method === "POST") return respond(EMPLOYEES[1], 201);
    if (url.includes("/hr/teams")) return respond({ items: TEAMS, next_cursor: null });
    return respond({ items: EMPLOYEES, next_cursor: null });
  });
  return calls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <EmployeesPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("EmployeesPage (R23)", () => {
  it("lists people with team, manager and an unambiguous start date, with no axe violations", async () => {
    mockApi();
    const { container } = renderPage();
    expect(await screen.findByText("Eli Employee")).toBeInTheDocument();
    expect(screen.getByText("Wed 1 Jul 2026")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("refuses a non-company email and shows the error summary", async () => {
    const user = userEvent.setup();
    const calls = mockApi();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Add employee" }));
    await user.type(screen.getByLabelText("Name"), "Gus");
    await user.type(screen.getByLabelText("Work email"), "gus@gmail.com");
    await user.click(screen.getByRole("button", { name: "Save employee" }));
    expect(await screen.findAllByText(/company email ending in @asnet.com.vn/)).not.toHaveLength(0);
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });

  it("re-sends an invite", async () => {
    const user = userEvent.setup();
    const calls = mockApi();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Re-send invite to Eli Employee" }));
    expect(await screen.findByText("Invite re-sent to Eli Employee.")).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST" && c.url.endsWith("/hr/employees/e/invite"))).toBe(true);
  });
});
