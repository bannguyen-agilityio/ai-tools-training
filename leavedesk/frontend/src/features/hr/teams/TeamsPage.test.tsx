import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { ToastProvider } from "../../../ui/Toast";
import { TeamsPage } from "./TeamsPage";

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockApi(conflict = false) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (init?.method === "POST")
      return conflict
        ? respond({ error: { code: "CONFLICT", message: "A team with that name already exists.", details: [] } }, 409)
        : respond({ id: "n", name: "New", manager_id: null }, 201);
    if (url.includes("/hr/teams")) return respond({ items: [{ id: "t", name: "Platform", manager_id: null }], next_cursor: null });
    return respond({ items: [], next_cursor: null });
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <TeamsPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("TeamsPage (R23)", () => {
  it("lists teams with no axe violations", async () => {
    mockApi();
    const { container } = renderPage();
    expect(await screen.findByText("Platform")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("requires a name and shows a server conflict", async () => {
    const user = userEvent.setup();
    mockApi(true);
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Add team" }));
    await user.click(screen.getByRole("button", { name: "Save team" }));
    expect((await screen.findAllByText("Enter the team name.")).length).toBeGreaterThan(0);
    await user.type(screen.getByLabelText("Team name"), "Platform");
    await user.click(screen.getByRole("button", { name: "Save team" }));
    expect(await screen.findByText("A team with that name already exists.")).toBeInTheDocument();
  });
});
