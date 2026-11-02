import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { SignOutButton } from "./SignOutButton";

afterEach(() => vi.unstubAllGlobals());

it("posts logout with the CSRF token, clears it and goes to sign-in", async () => {
  sessionStorage.setItem("leavedesk.csrf", "tok");
  const fetchMock = vi
    .fn()
    .mockResolvedValue(new Response(null, { status: 204 }));
  vi.stubGlobal("fetch", fetchMock);
  const assign = vi.fn();
  vi.stubGlobal("location", { ...window.location, assign });
  render(<SignOutButton />);
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  await waitFor(() => expect(assign).toHaveBeenCalledWith("/sign-in"));
  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toBe("/api/v1/auth/logout");
  expect(init.method).toBe("POST");
  expect(init.headers["X-CSRF-Token"]).toBe("tok");
  expect(sessionStorage.getItem("leavedesk.csrf")).toBeNull();
});

it("stays on the page and warns when logout fails (session may still be live)", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { code: "forbidden", message: "CSRF", details: [] } }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
  const assign = vi.fn();
  vi.stubGlobal("location", { ...window.location, assign });
  render(<SignOutButton />);
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not sign out");
  expect(assign).not.toHaveBeenCalled();
});
