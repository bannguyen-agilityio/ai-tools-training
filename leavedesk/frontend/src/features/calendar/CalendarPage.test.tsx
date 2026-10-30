import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "vitest-axe";
import { CalendarPage } from "./CalendarPage";

const ME = { id: "me", name: "Me", email: "me@asnet.com.vn", role: "employee", is_hr_deputy: false };

function entry(over: object) {
  return { employee_id: "a", employee_name: "Ann", date: "2026-06-08", slot: "am", leave_type: "annual", status: "approved", ...over };
}
const OFF = { employee_id: "s", employee_name: "Sam", date: "2026-06-09", label: "Off" };

function json(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
}

function mockApi(entries: unknown[], role = "employee", urls: string[] = []) {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-06-15T05:00:00Z"));
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    urls.push(url);
    if (url.endsWith("/me")) return json({ ...ME, role });
    if (url.includes("/hr/teams")) return json({ items: [{ id: "t1", name: "Platform", manager_id: null }] });
    return json({ month: "2026-06", team_id: null, entries });
  });
  return urls;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <CalendarPage />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("CalendarPage (R27)", () => {
  it("spells out Pending, shows half days, masks Sick as Off, and has no axe violations", async () => {
    mockApi([
      entry({}),
      entry({ slot: "pm" }),
      entry({ date: "2026-06-10", employee_id: "b", employee_name: "Bo", slot: "pm", status: "pending" }),
      { ...OFF, slot: "am" },
      { ...OFF, slot: "pm" },
    ]);
    const { container } = renderPage();
    expect(await screen.findByText("Ann: Annual")).toBeInTheDocument();
    expect(screen.getByText("Bo: Annual (Pending) (afternoon)")).toBeInTheDocument();
    expect(screen.getByText("Sam: Off")).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/sick/i);
    expect(screen.getByText("Mon 8 Jun 2026")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("shows each half of a day on its own line when the halves differ", async () => {
    mockApi([
      entry({ slot: "am" }),
      entry({ slot: "pm", status: "pending" }),
      { ...OFF, employee_id: "a", employee_name: "Ann", date: "2026-06-08", slot: "pm" },
    ]);
    renderPage();
    expect(await screen.findByText("Ann: Annual (morning)")).toBeInTheDocument();
    expect(screen.getByText("Ann: Annual (Pending) (afternoon)")).toBeInTheDocument();
    expect(screen.getByText("Ann: Off (afternoon)")).toBeInTheDocument();
  });

  it("offers no team filter to an employee and asks for the next month", async () => {
    const user = userEvent.setup();
    const urls = mockApi([]);
    renderPage();
    expect(await screen.findByText(/is on leave this month/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Team")).toBeNull();
    expect(urls.some((u) => u.includes("/hr/teams"))).toBe(false);
    await user.click(screen.getByRole("button", { name: "Next month" }));
    await vi.waitFor(() => expect(urls.some((u) => u.includes("month=2026-07"))).toBe(true));
    expect(urls.some((u) => u.includes("team_id"))).toBe(false);
  });

  it("lets HR filter by team", async () => {
    const user = userEvent.setup();
    const urls = mockApi([], "hr");
    renderPage();
    await screen.findByRole("option", { name: "Platform" });
    await user.selectOptions(screen.getByLabelText("Team"), "t1");
    await vi.waitFor(() => expect(urls.some((u) => u.includes("team_id=t1"))).toBe(true));
  });
});
