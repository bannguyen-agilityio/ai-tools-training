import { expect, test } from "@playwright/test";
import { email, outbox, PASSWORD, reseed, signIn, sql } from "../support";

// There are no sign-in, set-password, reset or sign-out screens yet (the /sign-in route is a stub),
// so the account rules are exercised through the API and the routes the SPA does have.
test.beforeEach(() => reseed());

const login = (page: import("@playwright/test").Page, e: string, password: string) =>
  page.request.post("/api/v1/auth/login", { data: { email: e, password } });

test("E2E-AUTH-1: sign in sets an HttpOnly cookie and the app shows the user", async ({ page }) => {
  await signIn(page, "emp1");
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "LeaveDesk" })).toBeVisible();
  expect(await page.evaluate(() => document.cookie)).not.toContain("session");
  const cookies = await page.context().cookies();
  expect(cookies.find((c) => c.name === "session")?.httpOnly).toBe(true);
});

test("E2E-AUTH-2/3: wrong password, unknown user and foreign domain look the same", async ({ page }) => {
  const wrong = await login(page, email("emp1"), "not-the-password-1");
  const unknown = await login(page, "nobody@asnet.com.vn", "not-the-password-1");
  expect(wrong.status()).toBe(401);
  expect(unknown.status()).toBe(401);
  expect((await wrong.json()).error.message).toBe((await unknown.json()).error.message);
  const foreign = await login(page, "x@gmail.com", PASSWORD);
  expect([401, 422]).toContain(foreign.status());
});

test("E2E-AUTH-4: repeated failures lock the account, even for the right password", async ({ page }) => {
  let last = 0;
  for (let i = 0; i < 12 && last !== 429; i++) last = (await login(page, email("emp3"), "wrong-password-9")).status();
  expect(last).toBe(429);
  expect((await login(page, email("emp3"), PASSWORD)).status()).toBe(429);
});

test("E2E-AUTH-5: signed out, the app sends you to sign-in with a return path", async ({ page }) => {
  await page.goto("/requests");
  await expect(page).toHaveURL(/\/sign-in\?next=%2Frequests/);
});

test("E2E-AUTH-6: after sign-out the session no longer works", async ({ page }) => {
  const csrf = await signIn(page, "emp1");
  expect((await page.request.get("/api/v1/me")).status()).toBe(200);
  expect((await page.request.post("/api/v1/auth/logout", { headers: { "X-CSRF-Token": csrf } })).status()).toBe(204);
  expect((await page.request.get("/api/v1/me")).status()).toBe(401);
});

test("E2E-AUTH-7: an invite link sets the password once", async ({ page }) => {
  const csrf = await signIn(page, "hr1");
  const made = await page.request.post("/api/v1/hr/employees", {
    data: { name: "Nia New", email: "nia@asnet.com.vn", role: "employee", start_date: new Date().toISOString().slice(0, 10) },
    headers: { "X-CSRF-Token": csrf },
  });
  expect(made.status(), await made.text()).toBe(201);
  const link = outbox("nia@asnet.com.vn")[0].body.match(/https?:\/\/\S+/)![0];
  const token = new URL(link).searchParams.get("token")!;
  const ctx = await page.context().browser()!.newContext({ baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8000" });
  const anon = ctx.request;
  const set = { data: { token, password: "Brand-New-Password-42" } };
  expect((await anon.post("/api/v1/auth/invite/accept", set)).status()).toBe(204);
  expect((await anon.post("/api/v1/auth/invite/accept", set)).status()).toBeGreaterThanOrEqual(400);
  expect((await anon.post("/api/v1/auth/login", { data: { email: "nia@asnet.com.vn", password: "Brand-New-Password-42" } })).status()).toBe(200);
  await ctx.close();
});

test("E2E-AUTH-8: reset request is generic for unknown emails; the link works once", async ({ page }) => {
  const known = await page.request.post("/api/v1/auth/reset/request", { data: { email: email("emp1") } });
  const unknown = await page.request.post("/api/v1/auth/reset/request", { data: { email: "nobody@asnet.com.vn" } });
  expect(known.status()).toBe(unknown.status());
  const link = outbox(email("emp1")).find((m) => m.template.includes("reset"))!.body.match(/https?:\/\/\S+/)![0];
  const token = new URL(link).searchParams.get("token")!;
  const set = { data: { token, password: "Another-Fresh-Password-77" } };
  expect((await page.request.post("/api/v1/auth/reset/confirm", set)).status()).toBe(204);
  expect((await page.request.post("/api/v1/auth/reset/confirm", set)).status()).toBeGreaterThanOrEqual(400);
  expect((await login(page, email("emp1"), PASSWORD)).status()).toBe(401);
});

test("E2E-AUTH-9: a weak password is refused", async ({ page }) => {
  const csrf = await signIn(page, "emp1");
  const r = await page.request.post("/api/v1/auth/password/change", {
    data: { current_password: PASSWORD, new_password: "password" },
    headers: { "X-CSRF-Token": csrf },
  });
  expect(r.status()).toBeGreaterThanOrEqual(400);
});

test("E2E-AUTH-10: a deactivated user's open session stops working", async ({ page }) => {
  await signIn(page, "emp2");
  sql("update employee set is_active=false where email='emp2@asnet.com.vn'");
  expect((await page.request.get("/api/v1/me")).status()).toBe(401);
});

test("E2E-SEC-2: a state-changing call without the CSRF header is rejected", async ({ page }) => {
  await signIn(page, "emp1");
  const r = await page.request.post("/api/v1/requests", {
    data: { leave_type: "annual", start_date: "2030-01-07", end_date: "2030-01-07", start_part: "full", end_part: "full" },
  });
  expect(r.status()).toBe(403);
});

test("E2E-PLAT-1: deep links serve the SPA; unknown API versions use the error envelope", async ({ page }) => {
  const v9 = await page.request.get("/api/v9/anything");
  expect(v9.status()).toBe(404);
  expect((await v9.json()).error.code).toBe("NOT_FOUND");
  await signIn(page, "emp1");
  await page.goto("/requests/new");
  await expect(page.getByRole("heading", { name: "Request leave" })).toBeVisible();
  await page.goto("/definitely-not-a-page");
  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
});

test("Gap: the invite link points at a screen that does not exist", async ({ page }) => {
  test.fail(true, "No /set-password screen yet: the emailed link lands on 'Page not found'.");
  await page.goto("/set-password?token=abc");
  await expect(page.getByRole("heading", { name: /password/i })).toBeVisible();
});
