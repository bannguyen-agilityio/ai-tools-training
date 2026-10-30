import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { ToastProvider } from "../../../ui/Toast";
import { SettingsPage } from "./SettingsPage";

const EMPLOYEES = [
  { id: "h", name: "Hana HR", email: "h@asnet.com.vn", role: "hr", is_hr_deputy: false, team_id: null, manager_id: null, start_date: "2024-01-02", is_active: true },
  { id: "e", name: "Eli Employee", email: "e@asnet.com.vn", role: "employee", is_hr_deputy: false, team_id: null, manager_id: null, start_date: "2024-01-02", is_active: true },
  { id: "x", name: "Gone Person", email: "g@asnet.com.vn", role: "employee", is_hr_deputy: false, team_id: null, manager_id: null, start_date: "2024-01-02", is_active: false },
];

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockApi(calls: { method: string; url: string; body?: string }[] = []) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    calls.push({ method, url, body: init?.body as string | undefined });
    if (url.endsWith("/hr/deputy")) {
      return json({ employee_id: method === "PUT" ? "e" : null, name: null, email: null });
    }
    return json({ items: EMPLOYEES, next_cursor: null });
  });
  return calls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <SettingsPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("SettingsPage (R36)", () => {
  it("offers only active non-HR people and has no axe violations", async () => {
    mockApi();
    const { container } = renderPage();
    const select = await screen.findByLabelText("Deputy HR admin");
    expect(select).toHaveTextContent("Eli Employee");
    expect(select).not.toHaveTextContent("Hana HR");
    expect(select).not.toHaveTextContent("Gone Person");
    expect(await axe(container)).toHaveNoViolations();
  });

  it("saves the chosen deputy", async () => {
    const user = userEvent.setup();
    const calls = mockApi();
    renderPage();
    const save = await screen.findByRole("button", { name: "Save deputy" });
    expect(save).toBeDisabled();
    await user.selectOptions(screen.getByLabelText("Deputy HR admin"), "e");
    await user.click(save);
    await vi.waitFor(() => expect(calls.find((c) => c.method === "PUT")?.body).toBe(JSON.stringify({ employee_id: "e" })));
  });
});
