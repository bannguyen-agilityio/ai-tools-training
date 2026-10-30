import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { MyRequests } from "./MyRequests";
import { NewRequest } from "./NewRequest";
import { RequestDetail } from "./RequestDetail";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function wrap(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/requests" element={<MyRequests />} />
          <Route path="/requests/new" element={<NewRequest />} />
          <Route path="/requests/:id" element={<RequestDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const base = {
  id: "r1",
  employee_id: "e1",
  start_date: "2026-11-02",
  start_part: "full",
  end_date: "2026-11-04",
  end_part: "full",
  working_days: 3,
  note: null,
  status: "pending",
  queue: "manager",
  assigned_to: "m1",
  submitted_at: "2026-10-30T00:00:00Z",
  notice_warning: false,
  version: 1,
  label: null,
};

afterEach(() => vi.restoreAllMocks());

describe("requests screens", () => {
  it("lists my requests with unambiguous dates", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({ items: [{ ...base, leave_type: "annual" }], next_cursor: null }),
    );
    wrap("/requests");
    expect(
      await screen.findByRole("link", {
        name: /Mon 2 Nov 2026 to Wed 4 Nov 2026/,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("3 days")).toBeInTheDocument();
  });

  it("shows Off for a masked Sick request and never a note", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({ ...base, leave_type: null, label: "Off" }),
    );
    wrap("/requests/r1");
    expect(await screen.findByText("Off")).toBeInTheDocument();
    expect(screen.queryByText(/sick/i)).toBeNull();
  });

  it("says so when the request cannot be viewed", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({ error: { code: "FORBIDDEN", message: "Not allowed" } }, 403),
    );
    wrap("/requests/r1");
    expect(await screen.findByRole("alert")).toHaveTextContent("cannot view");
  });

  it("shows the live day count and the server's inline error from the preview", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({
        valid: false,
        working_days: 2,
        per_year: [
          { year: 2026, days: 2, available_before: 1, available_after: -1 },
        ],
        errors: [
          {
            code: "INSUFFICIENT_BALANCE",
            field: null,
            message: "Not enough annual leave in 2026: short by 1 day.",
          },
        ],
      }),
    );
    wrap("/requests/new");
    await userEvent.type(screen.getByLabelText(/Start date/), "Mon 2 Nov 2026");
    await userEvent.type(screen.getByLabelText(/End date/), "Tue 3 Nov 2026");
    expect(await screen.findByText("2 days")).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "short by 1 day",
    );
  });

  describe("cancel (R16)", () => {
    function mockApi(status: string, onCancel?: () => void) {
      vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
        const url = String(input);
        if (url.endsWith("/me"))
          return json({
            id: "e1",
            name: "A",
            email: "a@x.test",
            role: "employee",
            is_hr_deputy: false,
          });
        if (url.endsWith("/cancel") && init?.method === "POST") {
          onCancel?.();
          return json({ ...base, status: "cancelled", version: 2 });
        }
        return json({ ...base, leave_type: "annual", status });
      });
    }

    it("offers no cancel button once the request is decided", async () => {
      mockApi("approved");
      wrap("/requests/r1");
      await screen.findByText("Approved");
      expect(
        screen.queryByRole("button", { name: /cancel request/i }),
      ).toBeNull();
    });

    it("confirms with the dates, defaults to Keep, then cancels", async () => {
      const onCancel = vi.fn();
      mockApi("pending", onCancel);
      wrap("/requests/r1");
      await userEvent.click(
        await screen.findByRole("button", { name: "Cancel request" }),
      );
      const dialog = await screen.findByRole("alertdialog");
      expect(dialog).toHaveTextContent("Mon 2 Nov 2026");
      expect(screen.getByRole("button", { name: "Keep" })).toHaveFocus();
      expect(onCancel).not.toHaveBeenCalled();
      await userEvent.click(
        within(dialog).getByRole("button", { name: "Cancel request" }),
      );
      expect(await screen.findByText("Cancelled")).toBeInTheDocument();
      expect(onCancel).toHaveBeenCalledOnce();
    });

    it("keeping closes the dialog without calling the API", async () => {
      const onCancel = vi.fn();
      mockApi("pending", onCancel);
      wrap("/requests/r1");
      await userEvent.click(
        await screen.findByRole("button", { name: "Cancel request" }),
      );
      await userEvent.click(screen.getByRole("button", { name: "Keep" }));
      expect(screen.queryByRole("alertdialog")).toBeNull();
      expect(onCancel).not.toHaveBeenCalled();
    });
  });

  it("shows the short-notice warning on the detail page", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({ ...base, leave_type: "annual", notice_warning: true }),
    );
    wrap("/requests/r1");
    expect(await screen.findByRole("status")).toHaveTextContent(/Short notice/);
  });

  it("shows no warning when notice is fine", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({ ...base, leave_type: "annual" }),
    );
    wrap("/requests/r1");
    await screen.findByText("Leave request");
    expect(screen.queryByRole("status")).toBeNull();
  });
});
