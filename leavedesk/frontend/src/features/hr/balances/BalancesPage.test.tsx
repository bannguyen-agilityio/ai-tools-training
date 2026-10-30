import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { ToastProvider } from "../../../ui/Toast";
import { BalancesPage } from "./BalancesPage";

const ROWS = [
  {
    employee_id: "e1",
    employee_name: "Eli Employee",
    email: "eli@asnet.com.vn",
    balances: [
      { leave_type_code: "annual", entitlement_remaining: "5.0", carried_remaining: "2.0", used: "0.0", reserved: "0.0", available: "7.0" },
      { leave_type_code: "sick", entitlement_remaining: "7.0", carried_remaining: "0.0", used: "0.0", reserved: "0.0", available: "7.0" },
    ],
  },
];
const SUMMARY = {
  employee_name: "Eli Employee",
  leave_type_code: "annual",
  leave_year: 2026,
  kind: "opening",
  days: "5.0",
  expires_on: null,
  resulting_available: "5.0",
};

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockApi(calls: { method: string; url: string; body?: string }[] = []) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    calls.push({ method, url, body: init?.body as string | undefined });
    if (url.endsWith("/preview")) return respond(SUMMARY);
    if (method === "POST") return respond({ id: "x" }, 201);
    if (url.includes("/employees/e1/balances")) {
      return respond({ employee_id: "e1", employee_name: "Eli Employee", leave_year: 2026, balances: [], ledger: [] });
    }
    return respond({ leave_year: 2026, items: ROWS });
  });
  return calls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <BalancesPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("BalancesPage (R24)", () => {
  it("lists balances with no axe violations", async () => {
    mockApi();
    const { container } = renderPage();
    expect(await screen.findByText("Eli Employee")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("refuses 41 days before calling the API", async () => {
    const user = userEvent.setup();
    const calls = mockApi();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Enter balances for Eli Employee" }));
    await user.type(screen.getByLabelText("Days"), "41");
    await user.click(screen.getByRole("button", { name: "Review entry" }));
    expect((await screen.findAllByText("Days must be between 0 and 40.")).length).toBeGreaterThan(0);
    expect(calls.some((c) => c.url.endsWith("/preview"))).toBe(false);
  });

  it("previews, shows the summary, and saves only after confirming", async () => {
    const user = userEvent.setup();
    const calls = mockApi();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Enter balances for Eli Employee" }));
    await user.type(screen.getByLabelText("Days"), "5");
    await user.click(screen.getByRole("button", { name: "Review entry" }));
    expect(await screen.findByText("Check this entry before saving")).toBeInTheDocument();
    expect(calls.filter((c) => c.method === "POST" && !c.url.endsWith("/preview"))).toHaveLength(0);
    await user.click(screen.getByRole("button", { name: "Save entry" }));
    expect(await screen.findByText("Starting balances")).toBeInTheDocument();
    const saved = calls.find((c) => c.method === "POST" && c.url.endsWith("/balance-entries"));
    expect(JSON.parse(saved?.body ?? "{}")).toEqual({
      leave_type_code: "annual",
      kind: "opening",
      days: 5,
      leave_year: new Date().getFullYear(),
    });
  });

  it("requires a reason for an adjustment", async () => {
    const user = userEvent.setup();
    mockApi();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Enter balances for Eli Employee" }));
    await user.selectOptions(screen.getByLabelText("Entry"), "adjustment");
    await user.type(screen.getByLabelText("Days"), "-2");
    await user.click(screen.getByRole("button", { name: "Review entry" }));
    expect((await screen.findAllByText("Enter the reason for the correction.")).length).toBeGreaterThan(0);
  });
});
