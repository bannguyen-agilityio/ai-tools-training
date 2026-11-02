import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import { Dashboard } from "./Dashboard";

type Role = "employee" | "manager" | "hr";
const annual = { leave_type: "annual", entitlement: 12, carried: 3, expires_on: "2026-12-31", carried_expired: false, used: 3, reserved: 1, available: 11 };
const sick = { leave_type: "sick", entitlement: 7, carried: 0, expires_on: null, carried_expired: false, used: 1, reserved: 0, available: 6 };
const req = (over: object) => ({
  id: "r1", employee_id: "e", leave_type: "annual", start_date: "2026-11-09", start_part: "full", end_date: "2026-11-09", end_part: "full",
  working_days: 1, note: null, status: "approved", queue: "", assigned_to: null, submitted_at: "2026-10-29T03:00:00Z", notice_warning: false, version: 1, label: null, ...over,
});

interface Opts { role?: Role; deputy?: boolean; annual?: object; balances?: "error"; requests?: unknown[]; approvals?: unknown[] }
let calls: string[];

function mockApi(o: Opts = {}) {
  calls = [];
  const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    calls.push(url);
    if (url.includes("/me/balances")) return o.balances === "error" ? json({ error: { code: "x", message: "x", details: [] } }, 500) : json({ year: 2026, balances: [o.annual ?? annual, sick] });
    if (url.includes("/me/requests")) return json({ items: url.includes("status=approved") ? (o.requests ?? [req({})]) : [] });
    if (url.includes("/approvals")) return json({ items: o.approvals ?? [] });
    if (url.endsWith("/me")) return json({ id: "u", name: "Ann Lee", email: "a@x", role: o.role ?? "employee", is_hr_deputy: o.deputy ?? false });
    return json({});
  });
}

function renderPage(role: Role = "employee", deputy = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.setQueryData(["me"], { id: "u", name: "Ann Lee", email: "a@x", role, is_hr_deputy: deputy });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-11-02T03:00:00Z") }));
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("Dashboard", () => {
  it("shows the page header and the three balance cards (R10)", async () => {
    mockApi();
    const { container } = renderPage();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Mon 2 Nov 2026 · Leave year 2026")).toBeInTheDocument();
    expect(await screen.findByText("Annual leave available")).toBeInTheDocument();
    expect(screen.getByText("of 15 days")).toBeInTheDocument();
    expect(screen.getByText("Sick leave available")).toBeInTheDocument();
    expect(screen.getByText("1 of 7 used")).toBeInTheDocument();
    expect(screen.getByLabelText("No balance")).toBeInTheDocument();
    expect(screen.getByText(/No limit/)).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("Annual caption hides carried at 0 and shows expiry otherwise", async () => {
    mockApi({ annual: { ...annual, carried: 0, expires_on: null } });
    renderPage();
    expect(await screen.findByText(/3 used · 1 reserved/)).toBeInTheDocument();
    expect(screen.queryByText(/carried/)).toBeNull();
  });

  it("shows carried expiry in warning text within 60 days", async () => {
    mockApi();
    renderPage();
    const part = await screen.findByText(/3 carried, expire Thu 31 Dec 2026/);
    expect(part).toHaveClass("text-warning");
  });

  it("does not warn when expiry is more than 60 days away", async () => {
    mockApi({ annual: { ...annual, expires_on: "2027-12-31" } });
    renderPage();
    expect(await screen.findByText(/3 carried, expire Fri 31 Dec 2027/)).not.toHaveClass("text-warning");
  });

  it("an employee sees no approvals card and makes no /approvals call", async () => {
    mockApi();
    renderPage("employee");
    await screen.findByText("Annual leave available");
    expect(screen.queryByText("Awaiting your decision")).toBeNull();
    expect(calls.some((c) => c.includes("/approvals"))).toBe(false);
  });

  it.each([
    ["manager", false],
    ["hr", false],
    ["employee", true],
  ] as const)("%s (deputy %s) sees the approvals card with count and oldest date", async (role, deputy) => {
    mockApi({ approvals: [{ ...req({ status: "pending", submitted_at: "2026-10-29T03:00:00Z" }) }, { ...req({ id: "r2", status: "pending", submitted_at: "2026-10-30T03:00:00Z" }) }] });
    renderPage(role, deputy);
    expect(await screen.findByText("Oldest submitted Thu 29 Oct")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review approvals →" })).toHaveAttribute("href", "/approvals");
    expect(calls.some((c) => c.includes("/approvals?scope=assigned"))).toBe(true);
  });

  it("shows Nothing waiting and no button at 0", async () => {
    mockApi({ approvals: [] });
    renderPage("manager");
    expect(await screen.findByText("Nothing waiting")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Review approvals/ })).toBeNull();
  });

  it("lists upcoming leave with badges", async () => {
    mockApi();
    renderPage();
    expect(await screen.findByText("Mon 9 Nov")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.getByText("Annual")).toBeInTheDocument();
  });

  it("shows the empty state", async () => {
    mockApi({ requests: [] });
    renderPage();
    expect(await screen.findByText("No upcoming leave")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Request leave" })).toHaveLength(2);
  });

  it("shows loading skeletons first", () => {
    mockApi();
    renderPage();
    expect(screen.getByText("Loading upcoming leave")).toBeInTheDocument();
  });

  it("shows an inline error with Retry while other cards still render", async () => {
    mockApi({ balances: "error" });
    renderPage();
    expect(await screen.findByText("Could not load your balances.")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Mon 9 Nov")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
