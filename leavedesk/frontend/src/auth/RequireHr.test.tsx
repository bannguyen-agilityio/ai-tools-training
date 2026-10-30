import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { RequireHr } from "./RequireHr";

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderGate() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/hr/holidays"]}>
        <RequireHr>
          <h1>Secret HR page</h1>
        </RequireHr>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("RequireHr", () => {
  it("shows the page to HR", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ role: "hr" }));
    renderGate();
    expect(await screen.findByRole("heading", { name: "Secret HR page" })).toBeInTheDocument();
  });

  it.each(["employee", "manager"])("tells a %s it is not allowed", async (role) => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ role }));
    renderGate();
    expect(await screen.findByRole("heading", { name: "Not allowed" })).toBeInTheDocument();
    expect(screen.queryByText("Secret HR page")).not.toBeInTheDocument();
  });

  it("never renders the page for a signed-out visitor (redirects to sign-in)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ error: { code: "UNAUTHENTICATED", message: "x" } }, 401));
    renderGate();
    expect(await screen.findByText("Loading...")).toBeInTheDocument();
    await vi.waitFor(() => expect(screen.queryByText("Loading...")).not.toBeInTheDocument());
    expect(screen.queryByText("Secret HR page")).not.toBeInTheDocument();
  });

  it("does not show the page when the access check fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ error: { code: "INTERNAL_ERROR", message: "x" } }, 500));
    renderGate();
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not check your access");
  });
});
