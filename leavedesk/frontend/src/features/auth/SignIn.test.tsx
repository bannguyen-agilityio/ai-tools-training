import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SignIn } from "./SignIn";

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/sign-in?next=%2Fapprovals"]}>
        <Routes>
          <Route path="/sign-in" element={<SignIn />} />
          <Route path="/approvals" element={<h1>Approvals page</h1>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe("SignIn", () => {
  it("asks for both fields before calling the API", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    renderPage();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("2 things need fixing");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("stores the CSRF token and returns to the page the user wanted", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ csrf_token: "tok" }));
    renderPage();
    await userEvent.type(screen.getByLabelText("Work email"), "hr@asnet.com.vn");
    await userEvent.type(screen.getByLabelText("Password"), "Correct-Horse-Battery-9");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { name: "Approvals page" })).toBeInTheDocument();
    expect(sessionStorage.getItem("leavedesk.csrf")).toBe("tok");
  });

  it("shows one generic message for a wrong email or password", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ error: { code: "unauthorized", message: "x" } }, 401));
    renderPage();
    await userEvent.type(screen.getByLabelText("Work email"), "hr@asnet.com.vn");
    await userEvent.type(screen.getByLabelText("Password"), "wrong-password-123");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Email or password is incorrect."));
  });
});
