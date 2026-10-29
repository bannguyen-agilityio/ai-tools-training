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
