import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { reseed, signIn, type Persona } from "../support";

// Runs once per desktop project (1280 and 1024 wide). The 360 px checks live in e2e/a11y.spec.ts.
test.beforeAll(() => reseed());

const SCREENS: [Persona, string][] = [
  ["emp1", "/"],
  ["emp1", "/requests"],
  ["emp1", "/requests/new"],
  ["emp1", "/calendar"],
  ["mgr1", "/approvals"],
  ["hr1", "/hr/leave"],
  ["hr1", "/hr/employees"],
  ["hr1", "/hr/balances"],
  ["hr1", "/hr/teams"],
  ["hr1", "/hr/holidays"],
  ["hr1", "/hr/settings"],
  ["hr1", "/hr/report"],
];

for (const [who, path] of SCREENS) {
  test.describe(`${path} as ${who}`, () => {
    test.beforeEach(async ({ page }) => {
      await signIn(page, who);
      await page.goto(path);
      await page.getByRole("main").getByRole("heading", { level: 1 }).waitFor();
    });

    test("E2E-A11Y-1: no horizontal scroll", async ({ page }) => {
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
      expect(overflow).toBe(false);
    });

    test("E2E-A11Y-3: no WCAG 2.1 AA violations", async ({ page }) => {
      const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
      expect(r.violations.map((v) => `${v.id}: ${v.nodes[0]?.html.slice(0, 80)}`)).toEqual([]);
    });

    test("content stays inside the viewport and the nav is reachable", async ({ page }) => {
      const vw = page.viewportSize()!.width;
      const wide = await page.evaluate(
        (w) => [...document.querySelectorAll("main *")].filter((el) => el.getBoundingClientRect().right > w + 1).length,
        vw,
      );
      expect(wide).toBe(0);
      await expect(page.getByRole("navigation", { name: "Main" })).toBeVisible();
    });
  });
}

test("E2E-A11Y-5: destructive dialog is accessible on desktop", async ({ page }) => {
  await signIn(page, "hr1");
  await page.goto("/hr/employees");
  await page.getByRole("button", { name: "Deactivate Eva Employee" }).click();
  await expect(page.getByRole("button", { name: "Keep" })).toBeFocused();
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(r.violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Deactivate Eva Employee" })).toBeFocused();
});
