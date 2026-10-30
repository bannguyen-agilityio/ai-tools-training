import { expect, test } from "@playwright/test";
import { reseed, signIn } from "../support";

test.beforeEach(() => reseed());

// CAL-1/2 (Sick as Off, other teams hidden) need leave on the calendar; they are covered by the
// API tests and listed as not yet covered in TEST-CASES.md.
test("E2E-CAL-1 (smoke): the calendar page loads for an employee", async ({ page }) => {
  await signIn(page, "emp2");
  await page.goto("/calendar");
  await expect(page.getByRole("heading", { name: "Team calendar" })).toBeVisible();
});

test("E2E-CAL-4: an invalid month in the API does not 500", async ({ page }) => {
  const csrf = await signIn(page, "emp1");
  const r = await page.request.get("/api/v1/calendar?month=0000-01", { headers: { "X-CSRF-Token": csrf } });
  expect([400, 422]).toContain(r.status());
});
