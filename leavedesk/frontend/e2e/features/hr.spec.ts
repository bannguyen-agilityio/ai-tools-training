import { expect, test } from "@playwright/test";
import { email, label, outbox, requestLeave, reseed, signIn, sql, workday, type Persona } from "../support";

test.beforeEach(() => reseed());

const HR_PATHS = ["/hr/leave", "/hr/employees", "/hr/balances", "/hr/teams", "/hr/holidays", "/hr/settings", "/hr/report"];

test.describe("HR access (E2E-HREMP-1, E2E-SEC-1)", () => {
  for (const who of ["emp1", "mgr1", "deputy"] as Persona[]) {
    test(`${who}: no HR links and no HR data`, async ({ page }) => {
      const csrf = await signIn(page, who);
      await page.goto("/");
      await expect(page.getByRole("link", { name: "Employees" })).toHaveCount(0);
      for (const api of ["/hr/employees", "/hr/balances", "/hr/holidays/impact?date=2026-12-25", "/hr/leave", "/hr/deputy", "/hr/reports/monthly?month=2026-11&format=csv"]) {
        const r = await page.request.get(`/api/v1${api}`, { headers: { "X-CSRF-Token": csrf } });
        expect(r.status(), `${who} ${api}`).toBe(403);
      }
      await page.goto("/hr/employees");
      await expect(page.getByRole("heading", { name: "Employees" })).toHaveCount(0);
    });
  }
  test("HR sees every HR screen", async ({ page }) => {
    await signIn(page, "hr1");
    for (const path of HR_PATHS) {
      await page.goto(path);
      await expect(page.getByRole("main").getByRole("heading", { level: 1 })).toBeVisible();
    }
  });
});

test.describe("Employees and teams (R23, R4, R9)", () => {
  test("E2E-HREMP-2/3: create employee queues one invite; wrong domain refused", async ({ page }) => {
    await signIn(page, "hr1");
    await page.goto("/hr/employees");
    await page.getByRole("button", { name: "Add employee" }).click();
    const form = page.getByRole("form", { name: "Add employee" });
    await form.getByLabel("Name").fill("Nia New");
    await form.getByLabel("Work email").fill("nia@gmail.com");
    await form.getByLabel("Start date").fill(label(workday(1)));
    await form.getByRole("button", { name: "Save employee" }).click();
    await expect(form.locator('[aria-invalid="true"]').first()).toBeFocused();
    await form.getByLabel("Work email").fill("nia@asnet.com.vn");
    await form.getByRole("button", { name: "Save employee" }).click();
    await expect(page.getByText("Nia New")).toBeVisible();
    const mails = outbox("nia@asnet.com.vn");
    expect(mails).toHaveLength(1);
    expect(mails[0].body).toMatch(/http/);
  });

  test("E2E-HREMP-7: deactivate keeps by default; deactivated user cannot sign in", async ({ page }) => {
    await signIn(page, "hr1");
    await page.goto("/hr/employees");
    await page.getByRole("button", { name: "Deactivate Eva Employee" }).click();
    await expect(page.getByRole("button", { name: "Keep" })).toBeFocused();
    await page.getByRole("button", { name: "Keep" }).click();
    expect(sql("select is_active from employee where email='emp2@asnet.com.vn'")[0]).toEqual({ is_active: true });
    await page.getByRole("button", { name: "Deactivate Eva Employee" }).click();
    await page.getByRole("button", { name: "Deactivate", exact: true }).click();
    await expect.poll(() => sql("select is_active from employee where email='emp2@asnet.com.vn'")[0]).toEqual({ is_active: false });
    const r = await page.request.post("/api/v1/auth/login", { data: { email: email("emp2"), password: "Correct-Horse-Battery-9" } });
    expect(r.status()).toBe(401);
  });

  test("E2E-HREMP-9 (smoke): Settings lists the seeded deputy", async ({ page }) => {
    await signIn(page, "hr1");
    await page.goto("/hr/settings");
    await expect(page.getByLabel("Deputy HR admin")).toBeVisible();
    await expect(page.getByLabel("Deputy HR admin")).toContainText("Dana Deputy");
  });
});

test.describe("Balances (R24)", () => {
  test("E2E-HRBAL-1..3: preview, confirm, ledger; second opening refused", async ({ page }) => {
    await signIn(page, "hr1");
    await page.goto("/hr/balances");
    await page.getByRole("button", { name: "Enter or correct balances for Olga Orphan" }).click();
    await page.getByLabel("Days", { exact: true }).fill("5");
    await page.getByRole("button", { name: "Review entry" }).click();
    await expect(page.getByText("Check this entry before saving")).toBeVisible();
    expect(sql("select count(*)::int as n from balance_entry where kind='opening'")[0]).toEqual({ n: 0 });
    await page.getByRole("button", { name: "Save entry" }).click();
    await expect(page.getByText("Entry saved for Olga Orphan.")).toBeVisible();
    // The toast sits over the last table row and intercepts clicks (see PR notes).
    await page.getByRole("button", { name: "Dismiss" }).click();
    expect(sql("select count(*)::int as n from balance_entry where kind='opening'")[0]).toEqual({ n: 1 });
    await page.getByRole("button", { name: "Enter or correct balances for Olga Orphan" }).click();
    await page.getByLabel("Days", { exact: true }).fill("5");
    await page.getByRole("button", { name: "Review entry" }).click();
    await expect(page.getByRole("alert").first()).toContainText(/already exists/i);
  });

  test("E2E-HRBAL-4: carried days over 6 are refused", async ({ page }) => {
    await signIn(page, "hr1");
    await page.goto("/hr/balances");
    await page.getByRole("button", { name: "Enter or correct balances for Olga Orphan" }).click();
    await page.getByLabel("Entry", { exact: true }).selectOption({ label: "Carried days (with expiry)" });
    await page.getByLabel("Days", { exact: true }).fill("6.5");
    await page.getByLabel("Carried days expire on").fill(`Thu 31 Dec ${new Date().getFullYear()}`);
    await page.getByRole("button", { name: "Review entry" }).click();
    await expect(page.locator(".form-error", { hasText: "Carried days are at most 6." })).toBeVisible();
  });

  test("E2E-HRBAL-6: a negative result shows a warning on the confirm step", async ({ page }) => {
    await signIn(page, "hr1");
    await page.goto("/hr/balances");
    await page.getByRole("button", { name: "Enter or correct balances for Olga Orphan" }).click();
    await page.getByLabel("Entry", { exact: true }).selectOption({ label: "Correction (adjustment)" });
    await page.getByLabel("Days", { exact: true }).fill("-20");
    await page.getByLabel("Reason").fill("test");
    await page.getByRole("button", { name: "Review entry" }).click();
    await expect(page.getByText(/negative balance/)).toBeVisible();
  });
});

test.describe("Holidays (R11)", () => {
  test("E2E-HOL-3: adding a holiday on a day with leave leaves working_days unchanged", async ({ page }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { start: workday(20) });
    await page.waitForURL(/\/requests\/[0-9a-f-]+$/);
    const before = sql("select working_days from leave_request")[0];
    const csrf = await signIn(page, "hr1");
    await page.goto("/hr/holidays");
    await expect(page.getByRole("button", { name: /^Edit .* on / }).first()).toBeVisible();
    const d = workday(20).toISOString().slice(0, 10);
    const res = await page.request.post("/api/v1/hr/holidays", { data: { holiday_date: d, name: "E2E day" }, headers: { "X-CSRF-Token": csrf } });
    expect(res.status(), await res.text()).toBe(201);
    expect(sql("select working_days from leave_request")[0]).toEqual(before);
  });
});

test.describe("All leave and report (R25, R28)", () => {
  test("E2E-ALL-1: HR sees approved leave incl. Sick type", async ({ page, browser }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { type: "Sick", start: workday(1) });
    await page.waitForURL(/\/requests\/[0-9a-f-]+$/);
    sql("update leave_request set status='approved'");
    const ctx = await browser.newContext();
    const hr = await ctx.newPage();
    await signIn(hr, "hr1");
    await hr.goto("/hr/leave");
    await expect(hr.getByRole("link", { name: "Eli Employee" })).toBeVisible();
    await expect(hr.getByRole("table").getByText("Sick", { exact: true })).toBeVisible();
    await ctx.close();
  });

  test("E2E-REP-2/3: export is marked confidential and audited", async ({ page }) => {
    const csrf = await signIn(page, "hr1");
    const month = new Date().toISOString().slice(0, 7);
    const r = await page.request.get(`/api/v1/hr/reports/monthly?month=${month}&format=csv`, { headers: { "X-CSRF-Token": csrf } });
    expect(r.status(), await r.text()).toBe(200);
    const text = await r.text();
    expect(text.toLowerCase()).toContain("confidential");
    // HR-only by design (spec R28, C-13): the file may carry types, so the banner and audit are the controls.
    expect(sql("select count(*)::int as n from audit_log where action like '%report%'")[0].n).toBeGreaterThan(0);
  });
});
