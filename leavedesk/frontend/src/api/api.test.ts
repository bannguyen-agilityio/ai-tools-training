import { api, safeNext, setCsrfToken, signInUrl } from "./client";
import { ApiError, parseProblem } from "./problem";

function respond(status: number, body?: unknown, contentType = "application/json") {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": contentType },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe("parseProblem", () => {
  it("reads the spec error envelope", async () => {
    const err = await parseProblem(
      respond(422, { error: { code: "invalid", message: "Fix it", details: [{ field: "a", message: "bad" }] } }),
    );
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("invalid");
    expect(err.fields).toEqual([{ field: "a", message: "bad" }]);
  });
  it("reads problem+json", async () => {
    const err = await parseProblem(respond(403, { title: "Forbidden", detail: "No" }, "application/problem+json"));
    expect(err.message).toBe("No");
    expect(err.status).toBe(403);
  });
});

describe("api client", () => {
  it("sends the CSRF header on state-changing calls only", async () => {
    setCsrfToken("tok");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async () => respond(200, {}));
    await api("/x");
    await api("/x", { method: "POST", body: {} });
    const [get, post] = fetchMock.mock.calls.map((c) => c[1]?.headers as Record<string, string>);
    expect(get["X-CSRF-Token"]).toBeUndefined();
    expect(post["X-CSRF-Token"]).toBe("tok");
  });
  it("throws ApiError on failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond(409, { error: { code: "stale", message: "Changed" } }));
    await expect(api("/x", { method: "POST" })).rejects.toMatchObject({ status: 409, code: "stale" });
  });
  it("redirects to sign-in preserving the return path on 401", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(respond(401, { title: "Unauthorized" }));
    const assign = vi.fn();
    vi.stubGlobal("location", { pathname: "/requests", search: "?a=1", assign });
    await expect(api("/me")).rejects.toBeInstanceOf(ApiError);
    expect(assign).toHaveBeenCalledWith(signInUrl("/requests?a=1"));
    vi.unstubAllGlobals();
  });
});

describe("safeNext", () => {
  it("only allows same-site relative paths", () => {
    expect(safeNext("/requests")).toBe("/requests");
    expect(safeNext("//evil.com")).toBe("/");
    expect(safeNext("https://evil.com")).toBe("/");
    expect(safeNext(null)).toBe("/");
  });
});
