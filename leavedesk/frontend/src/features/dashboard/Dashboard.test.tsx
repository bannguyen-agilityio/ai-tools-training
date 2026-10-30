import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { axe } from "vitest-axe";
import { Dashboard } from "./Dashboard";

const body = {
  year: 2026,
  balances: [
    { leave_type: "annual", entitlement: 12, carried: 3, expires_on: "2026-12-31", carried_expired: false, used: 4, reserved: 2, available: 9 },
    { leave_type: "sick", entitlement: 7, carried: 0, expires_on: null, carried_expired: false, used: 0, reserved: 0, available: 7 },
  ],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("Dashboard (R10)", () => {
  it("shows per type balances with the carry-over expiry date", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    const { container } = renderPage();
    expect(await screen.findByText("9 days available")).toBeInTheDocument();
    expect(screen.getByText("3 days, expire Thu 31 Dec 2026")).toBeInTheDocument();
    expect(screen.getByText("7 days available")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Request leave" })).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });
});
