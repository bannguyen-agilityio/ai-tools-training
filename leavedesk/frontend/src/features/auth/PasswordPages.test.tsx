import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ChangePassword } from "./ChangePassword";
import { ForgotPassword } from "./ForgotPassword";
import { ResetPassword } from "./ResetPassword";
import { SetPassword } from "./SetPassword";
import { SignIn } from "./SignIn";

function respond(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/set-password" element={<SetPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/account/password" element={<ChangePassword />} />
          <Route path="/sign-in" element={<SignIn />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const GOOD = "correct horse battery";

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe("SetPassword / ResetPassword", () => {
  it("tells an invitee with a bad link to ask HR", () => {
    renderAt("/set-password");
    expect(screen.getByRole("heading", { name: /expired or was already used/ })).toBeInTheDocument();
    expect(screen.getByText(/Ask HR to send you a new invite/)).toBeInTheDocument();
  });

  it("offers a reset-link request when a reset link is bad", () => {
    renderAt("/reset-password");
    expect(screen.getByRole("link", { name: "Request a new link" })).toHaveAttribute("href", "/forgot-password");
  });

  it("refuses short or mismatched passwords before calling the API", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    renderAt("/set-password?token=abc");
    await userEvent.type(screen.getByLabelText("New password"), "short");
    await userEvent.type(screen.getByLabelText("Confirm new password"), "other");
    await userEvent.click(screen.getByRole("button", { name: "Set password" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("2 things need fixing");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("posts the token and password, then goes to sign in", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    renderAt("/set-password?token=abc");
    await userEvent.type(screen.getByLabelText("New password"), GOOD);
    await userEvent.type(screen.getByLabelText("Confirm new password"), GOOD);
    await userEvent.click(screen.getByRole("button", { name: "Set password" }));
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Password saved");
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/auth/invite/accept");
    expect(JSON.parse(init.body as string)).toEqual({ token: "abc", password: GOOD });
  });

  it("shows the expired-link page when the server says the link is bad", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ error: { code: "bad_request", message: "x" } }, 400));
    renderAt("/reset-password?token=abc");
    await userEvent.type(screen.getByLabelText("New password"), GOOD);
    await userEvent.type(screen.getByLabelText("Confirm new password"), GOOD);
    await userEvent.click(screen.getByRole("button", { name: "Reset password" }));
    expect(await screen.findByRole("heading", { name: /expired or was already used/ })).toBeInTheDocument();
  });

  it("keeps the form and shows the server's policy message on 422", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respond({ error: { code: "validation_error", message: "That password is too common. Choose a different one." } }, 422),
    );
    renderAt("/set-password?token=abc");
    await userEvent.type(screen.getByLabelText("New password"), "password1234");
    await userEvent.type(screen.getByLabelText("Confirm new password"), "password1234");
    await userEvent.click(screen.getByRole("button", { name: "Set password" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("too common");
  });
});

describe("ForgotPassword", () => {
  it("shows the same confirmation whatever the server does with the address", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond({ status: "accepted" }, 202));
    renderAt("/forgot-password");
    await userEvent.type(screen.getByLabelText("Work email"), "nobody@asnet.com.vn");
    await userEvent.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByRole("status")).toHaveTextContent("If that address belongs");
  });

  it("asks for the email first", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    renderAt("/forgot-password");
    await userEvent.click(screen.getByRole("button", { name: "Send reset link" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("1 thing needs fixing");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});

describe("ChangePassword", () => {
  it("tells a failed CSRF/Origin check apart from a wrong password", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respond({ error: { code: "forbidden", message: "Cross-origin request refused" } }, 403),
    );
    renderAt("/account/password");
    await userEvent.type(screen.getByLabelText("Current password"), "right");
    await userEvent.type(screen.getByLabelText("New password"), GOOD);
    await userEvent.type(screen.getByLabelText("Confirm new password"), GOOD);
    await userEvent.click(screen.getByRole("button", { name: "Change password" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("could not be verified"));
  });

  it("reports a wrong current password", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respond({ error: { code: "forbidden", message: "Current password is incorrect" } }, 403),
    );
    renderAt("/account/password");
    await userEvent.type(screen.getByLabelText("Current password"), "wrong");
    await userEvent.type(screen.getByLabelText("New password"), GOOD);
    await userEvent.type(screen.getByLabelText("Confirm new password"), GOOD);
    await userEvent.click(screen.getByRole("button", { name: "Change password" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("current password is incorrect"));
  });
});
