import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { ToastProvider } from "../../../ui/Toast";
import { HolidaysPage } from "./HolidaysPage";

const HOLIDAYS = [
  { id: "a", holiday_date: "2026-09-01", name: "National Day", source: "seed" },
  { id: "b", holiday_date: "2026-09-02", name: "National Day", source: "seed" },
];

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockApi(impact: number, calls: { method: string; url: string }[] = []) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    calls.push({ method, url });
    if (url.includes("/hr/holidays/impact")) return respond({ holiday_date: "x", affected_requests: impact });
    if (method === "DELETE") return respond({ holiday: HOLIDAYS[0], affected_requests: impact });
    if (method === "POST") return respond({ holiday: HOLIDAYS[0], affected_requests: impact }, 201);
    return respond(HOLIDAYS);
  });
  return calls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <HolidaysPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("HolidaysPage (R11)", () => {
  it("lists holidays with unambiguous dates and has no axe violations", async () => {
    mockApi(0);
    const { container } = renderPage();
    expect(await screen.findByText("Tue 1 Sep 2026")).toBeInTheDocument();
    expect(screen.getByText("Wed 2 Sep 2026")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("states how many requests a delete affects and defaults focus to Keep", async () => {
    const user = userEvent.setup();
    const calls = mockApi(3);
    renderPage();
    await user.click(await screen.findByRole("button", { name: /Delete National Day on Tue 1 Sep 2026/ }));
    const dialog = await screen.findByRole("alertdialog");
    expect(await within(dialog).findByText(/3 requests affected/)).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Keep" })).toHaveFocus();
    await user.click(within(dialog).getByRole("button", { name: "Keep" }));
    expect(calls.some((c) => c.method === "DELETE")).toBe(false);
  });

  it("deletes only after confirming", async () => {
    const user = userEvent.setup();
    const calls = mockApi(1);
    renderPage();
    await user.click(await screen.findByRole("button", { name: /Delete National Day on Tue 1 Sep 2026/ }));
    const dialog = await screen.findByRole("alertdialog");
    await within(dialog).findByText(/1 request affected/);
    await user.click(within(dialog).getByRole("button", { name: "Delete holiday" }));
    expect(await screen.findByText(/Holiday deleted\. 1 request affected\./)).toBeInTheDocument();
    expect(calls.filter((c) => c.method === "DELETE")).toHaveLength(1);
  });

  it("shows the impact while adding and focuses the first error on a bad submit", async () => {
    const user = userEvent.setup();
    const calls = mockApi(2);
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Add holiday" }));
    await user.click(screen.getByRole("button", { name: "Save holiday" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("2 things need fixing");
    expect(screen.getByLabelText("Date")).toHaveFocus();
    await user.type(screen.getByLabelText("Date"), "Fri 20 Nov 2026");
    await user.type(screen.getByLabelText("Name"), "Teachers' Day");
    expect(await screen.findByText("2 requests affected on this date.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Save holiday" }));
    expect(await screen.findByText(/Holiday added\. 2 requests affected\./)).toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST")).toBe(true);
  });
});
