import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const path of ["/", "/sample-form"]) {
  test.describe(`360px ${path}`, () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(path);
      await page.locator("main").waitFor();
    });

    test("R31a: no horizontal scroll", async ({ page }) => {
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
      );
      expect(overflow).toBe(false);
    });

    test("R31a: targets are at least 44px", async ({ page }) => {
      const small = await page.evaluate(() =>
        [...document.querySelectorAll<HTMLElement>("button, a[href]:not(.skip-link), input, select")]
          .map((el) => ({ el: el.outerHTML.slice(0, 60), r: el.getBoundingClientRect() }))
          .filter(({ r }) => r.height < 44 || r.width < 44)
          .map(({ el }) => el),
      );
      expect(small).toEqual([]);
    });

    test("R31b: no WCAG 2.1 AA violations", async ({ page }) => {
      const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
      expect(results.violations).toEqual([]);
    });
  });
}

test.describe("360px /hr/holidays (R11, R31)", () => {
  const holidays = [
    { id: "a", holiday_date: "2026-09-01", name: "National Day", source: "seed" },
    { id: "b", holiday_date: "2026-09-02", name: "National Day", source: "seed" },
  ];

  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/me", (r) => r.fulfill({ json: { id: "x", name: "HR", email: "hr@asnet.com.vn", role: "hr", is_hr_deputy: false } }));
    await page.route("**/api/v1/holidays?*", (r) => r.fulfill({ json: { items: holidays, next_cursor: null } }));
    await page.route("**/api/v1/hr/holidays/impact?*", (r) => r.fulfill({ json: { holiday_date: "2026-09-01", affected_requests: 3 } }));
    await page.goto("/hr/holidays");
    await page.getByRole("heading", { name: /Public holidays/ }).waitFor();
  });

  const targets = () =>
    [...document.querySelectorAll<HTMLElement>("button, a[href]:not(.skip-link), input, select")]
      .map((el) => ({ el: el.outerHTML.slice(0, 60), r: el.getBoundingClientRect() }))
      .filter(({ r }) => r.height < 44 || r.width < 44)
      .map(({ el }) => el);

  test("list: no horizontal scroll, 44px targets, no AA violations", async ({ page }) => {
    expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
    expect(await page.evaluate(targets)).toEqual([]);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    expect(results.violations).toEqual([]);
  });

  test("delete confirmation: states the impact, focus starts on Keep, no AA violations", async ({ page }) => {
    await page.getByRole("button", { name: /Delete National Day on Tue 1 Sep 2026/ }).click();
    const dialog = page.getByRole("alertdialog");
    await expect(dialog).toContainText("3 requests affected");
    await expect(dialog.getByRole("button", { name: "Keep" })).toBeFocused();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    expect(results.violations).toEqual([]);
  });

  test("add form: no horizontal scroll, 44px targets, no AA violations", async ({ page }) => {
    await page.getByRole("button", { name: "Add holiday" }).click();
    await page.getByRole("button", { name: "Save holiday" }).click();
    await expect(page.getByRole("alert").first()).toContainText("2 things need fixing");
    await expect(page.getByLabel("Date")).toBeFocused();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
    expect(await page.evaluate(targets)).toEqual([]);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    expect(results.violations).toEqual([]);
  });
});
