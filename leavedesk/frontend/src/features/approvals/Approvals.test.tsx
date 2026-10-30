import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { ApprovalList } from "./ApprovalList";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const item = {
  id: "r1",
  employee_id: "e1",
  leave_type: "sick",
  start_date: "2026-11-02",
  start_part: "full",
  end_date: "2026-11-04",
  end_part: "full",
  working_days: 3,
  note: "flu",
  status: "pending",
  queue: "manager",
  assigned_to: "m1",
  submitted_at: "2026-10-30T00:00:00Z",
  notice_warning: false,
  version: 4,
  label: null,
  employee_name: "An Nguyen",
};

function mount() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ApprovalList />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("approvals", () => {
  it("shows who is asking", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => json({ items: [item] }));
    mount();
    expect(await screen.findByText("An Nguyen")).toBeInTheDocument();
  });

  it("shows the note and type while deciding, and approves with the version", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (input, init) =>
        String(input).endsWith("/approve") && init?.method === "POST"
          ? json({ ...item, status: "approved" })
          : json({ items: [item] }),
      );
    mount();
    expect(await screen.findByText("flu")).toBeInTheDocument();
    expect(screen.getByText("Sick")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(await screen.findByRole("status")).toHaveTextContent("approved");
    const post = fetchMock.mock.calls.find(([, i]) => i?.method === "POST");
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({ version: 4 });
  });

  it("refuses an empty reason inline and focuses the field", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      json({ items: [item] }),
    );
    mount();
    await userEvent.click(await screen.findByRole("button", { name: "Reject" }));
    await userEvent.type(screen.getByLabelText(/Reason for rejecting/), "   ");
    await userEvent.click(
      screen.getByRole("button", { name: "Reject request" }),
    );
    expect(screen.getByText(/Enter a reason/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Reason for rejecting/)).toHaveFocus();
  });

  it("shows the server message when someone decided first", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) =>
      init?.method === "POST"
        ? json(
            {
              error: {
                code: "ALREADY_DECIDED",
                message: "This request was already decided.",
              },
            },
            409,
          )
        : json({ items: [item] }),
    );
    mount();
    await userEvent.click(await screen.findByRole("button", { name: "Approve" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This request was already decided.",
    );
  });
});
