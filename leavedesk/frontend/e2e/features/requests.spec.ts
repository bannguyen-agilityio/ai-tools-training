import { expect, test } from "@playwright/test";
import { label, requestLeave, reseed, signIn, sql, workday } from "../support";

test.beforeEach(() => reseed());

test.describe("New request (R12-R14)", () => {
  test("E2E-REQ-1/2: Annual Mon-Fri shows the day count and lands as Pending", async ({ page }) => {
    await signIn(page, "emp1");
    await page.goto("/requests/new");
    await page.getByLabel("Start date").fill(label(workday(8)));
    await page.getByLabel("End date").fill(label(workday(12)));
    await expect(page.getByText("5 days", { exact: true })).toBeVisible();
    await expect(page.getByText(/left after this request/)).toBeVisible();
    await page.getByRole("button", { name: "Submit request" }).click();
    await expect(page).toHaveURL(/\/requests\/[0-9a-f-]+$/);
    await expect(page.getByText("Pending")).toBeVisible();
  });

  test("E2E-REQ-4: half day counts 0.5", async ({ page }) => {
    await signIn(page, "emp1");
    await page.goto("/requests/new");
    const d = label(workday(8));
    await page.getByLabel("Start date").fill(d);
    await page.getByLabel("End date").fill(d);
    await page.getByLabel("Which part of the day").selectOption({ label: "Morning" });
    await expect(page.getByText("0.5 days")).toBeVisible();
  });

  test("E2E-REQ-6: end before start shows an error", async ({ page }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { start: workday(10), end: workday(8) });
    await expect(page.locator('[aria-invalid="true"]').first()).toBeFocused();
  });

  test("E2E-REQ-7: overlap is refused", async ({ page }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { start: workday(8), end: workday(9) });
    await expect(page).toHaveURL(/\/requests\/[0-9a-f-]+$/);
    await requestLeave(page, { start: workday(9), end: workday(10) });
    await expect(page).toHaveURL(/\/requests\/new$/);
    await expect(page.getByRole("alert").first()).toBeVisible();
  });

  test("E2E-REQ-8: past start is refused", async ({ page }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { start: new Date(Date.now() - 10 * 86400000) });
    await expect(page).toHaveURL(/\/requests\/new$/);
    await expect(page.getByRole("alert").first()).toBeVisible();
  });

  test("E2E-REQ-10: more than the available balance is refused", async ({ page }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { start: workday(8), end: workday(30) });
    await expect(page).toHaveURL(/\/requests\/new$/);
    await expect(page.getByRole("alert").first()).toBeVisible();
  });

  test("E2E-REQ-11: single-day Annual starting today is blocked", async ({ page }) => {
    await signIn(page, "emp1");
    test.skip([0, 6].includes(new Date().getUTCDay()), "today is not a working day");
    await requestLeave(page, { start: new Date() });
    await expect(page).toHaveURL(/\/requests\/new$/);
    await expect(page.getByRole("alert").first()).toBeVisible();
  });

  test("E2E-REQ-13: Sick today has no notice block", async ({ page }) => {
    await signIn(page, "emp1");
    const today = new Date();
    const wd = today.getUTCDay();
    test.skip(wd === 0 || wd === 6, "today is not a working day");
    await requestLeave(page, { type: "Sick", start: today });
    await expect(page).toHaveURL(/\/requests\/[0-9a-f-]+$/);
  });

  test("E2E-REQ-16: double click submits once", async ({ page }) => {
    await signIn(page, "emp1");
    await page.goto("/requests/new");
    await page.getByLabel("Start date").fill(label(workday(8)));
    await page.getByLabel("End date").fill(label(workday(8)));
    await page.getByRole("button", { name: "Submit request" }).dblclick();
    await expect(page).toHaveURL(/\/requests\/[0-9a-f-]+$/);
    expect(sql("select count(*)::int as n from leave_request")[0]).toEqual({ n: 1 });
  });

  test("E2E-REQ-18: employee without a manager is refused", async ({ page }) => {
    await signIn(page, "orphan");
    await requestLeave(page, { start: workday(8) });
    await expect(page).toHaveURL(/\/requests\/new$/);
    await expect(page.getByRole("alert").first()).toBeVisible();
    expect(sql("select count(*)::int as n from leave_request")[0]).toEqual({ n: 0 });
  });

  test("E2E-REQ-19: a manager's request is routed to HR, an HR admin's to the deputy", async ({ page }) => {
    await signIn(page, "mgr1");
    await requestLeave(page, { start: workday(8) });
    await expect(page).toHaveURL(/\/requests\/[0-9a-f-]+$/);
    expect(sql("select queue from leave_request")[0]).toEqual({ queue: "hr" });
    await page.context().clearCookies();
    await signIn(page, "hr1");
    await requestLeave(page, { start: workday(15) });
    expect(sql("select queue from leave_request order by submitted_at desc")[0]).toEqual({ queue: "deputy" });
  });

  test("E2E-REQ-20: date field rejects gibberish", async ({ page }) => {
    await signIn(page, "emp1");
    await page.goto("/requests/new");
    await page.getByLabel("Start date").fill("someday");
    await expect(page.getByText(/Not a date/)).toBeVisible();
  });
});

test.describe("Dashboard and My requests (R10, R16)", () => {
  test("E2E-DASH-1/2: balances reserve days on submit", async ({ page }) => {
    await signIn(page, "emp1");
    await page.goto("/");
    const annual = page.getByRole("heading", { name: "Annual" }).locator("..");
    await expect(annual).toContainText("12");
    await requestLeave(page, { start: workday(8), end: workday(9) });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Annual" }).locator("..")).toContainText("10");
  });

  test("E2E-DASH-5: carried days show an expiry date", async ({ page }) => {
    await signIn(page, "emp2");
    await page.goto("/");
    await expect(page.getByText(/31 Dec/).first()).toBeVisible();
  });

  test("E2E-MY-1/2/4: list, detail, cancel with Keep as the default", async ({ page }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { start: workday(8) });
    await page.goto("/requests");
    await page.getByRole("link", { name: new RegExp(label(workday(8))) }).click();
    await page.getByRole("button", { name: "Cancel request" }).click();
    const dialog = page.getByRole("alertdialog");
    await expect(dialog.getByRole("button", { name: "Keep" })).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(page.getByText("Pending")).toBeVisible();
    await page.getByRole("button", { name: "Cancel request" }).click();
    await dialog.getByRole("button", { name: "Cancel request" }).click();
    await expect(page.getByText("Cancelled", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Cancel request" })).toHaveCount(0);
  });

  test("E2E-MY-3: another employee's request is not viewable", async ({ page, browser }) => {
    await signIn(page, "emp1");
    await requestLeave(page, { start: workday(8) });
    await page.waitForURL(/\/requests\/[0-9a-f-]+$/);
    const id = page.url().split("/").pop();
    const other = await browser.newContext();
    const p2 = await other.newPage();
    await signIn(p2, "emp3");
    await p2.goto(`/requests/${id}`);
    // react-query retries the 403 three times with back-off before the error shows (see PR notes).
    await expect(p2.getByText("You cannot view this request.")).toBeVisible({ timeout: 20_000 });
    await other.close();
  });
});
