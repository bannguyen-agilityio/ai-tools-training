import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { useMe } from "./useMe";

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe("useMe", () => {
  it("stores the CSRF token from /me so a new tab can still POST", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: "1", name: "A", email: "a@asnet.com.vn", role: "hr", is_hr_deputy: false, csrf_token: "tok-123" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    const { result } = renderHook(() => useMe(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(sessionStorage.getItem("leavedesk.csrf")).toBe("tok-123");
  });
});
