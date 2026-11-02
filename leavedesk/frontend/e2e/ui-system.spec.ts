import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * Visual system checks (R31): every P1 screen at 360 and 1280 px in light and dark.
 * The API is mocked in the browser, so only the built bundle and the real CSP headers
 * from FastAPI are under test. Screenshots land in test-results/.
 */
type Role = "employee" | "manager" | "hr";
const now = "2026-11-02T03:00:00Z";
const req = (id: string, o: object = {}) => ({
  id, employee_id: "e", employee_name: "Binh Tran", leave_type: "annual", start_date: "2026-11-09", start_part: "full",
  end_date: "2026-11-09", end_part: "full", working_days: 1, note: null, status: "approved", queue: "", assigned_to: null,
  submitted_at: "2026-10-29T03:00:00Z", notice_warning: false, version: 1, label: null, ...o,
});
const balances = {
  year: 2026,
  balances: [
    { leave_type: "annual", entitlement: 12, carried: 3, expires_on: "2026-12-31", carried_expired: false, used: 3, reserved: 1, available: 11 },
    { leave_type: "sick", entitlement: 7, carried: 0, expires_on: null, carried_expired: false, used: 1, reserved: 0, available: 6 },
  ],
};
const list = [
  req("1"),
  req("2", { start_date: "2026-12-23", end_date: "2026-12-23", start_part: "am", status: "pending", working_days: 0.5 }),
  req("3", { start_date: "2026-12-28", end_date: "2026-12-30", working_days: 2.5, leave_type: "unpaid" }),
  req("4", { leave_type: null, label: "Off", start_date: "2026-11-16", end_date: "2026-11-16" }),
];

async function mock(page: Page, role: Role) {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const p = url.pathname.replace("/api/v1", "");
    const json = (b: unknown) => route.fulfill({ json: b });
    if (p === "/me") return json({ id: "u", name: "Ann Lee", email: "a@asnet.com.vn", role, is_hr_deputy: false, csrf_token: "t" });
    if (p === "/me/balances") return json(balances);
    if (p === "/me/requests") return json({ items: list.filter((r) => url.searchParams.get("status") !== "pending" || r.status === "pending"), next_cursor: null });
    if (p === "/approvals") return json({ items: [req("9", { status: "pending", employee_name: "Cuong Le" })] });
    if (p === "/notifications") return json({ unread_count: 2, items: [{ id: "n", kind: "k", title: "Request approved", body: "Mon 9 Nov", link: "/requests/1", read_at: null, created_at: now }] });
    if (p.startsWith("/requests/") && p !== "/requests/preview") return json(list[0]);
    return json({ items: [], balances: [], ledger: [], pages: [] });
  });
}

const SCREENS: [string, string, Role][] = [
  ["sign-in", "/sign-in", "employee"],
  ["forgot", "/forgot-password", "employee"],
  ["dashboard-employee", "/", "employee"],
  ["dashboard-manager", "/", "manager"],
  ["my-requests", "/requests", "employee"],
  ["new-request", "/requests/new", "employee"],
  ["request-detail", "/requests/1", "employee"],
  ["approvals", "/approvals", "manager"],
  ["hr-leave", "/hr/leave", "hr"],
  ["hr-employees", "/hr/employees", "hr"],
  ["hr-balances", "/hr/balances", "hr"],
  ["hr-holidays", "/hr/holidays", "hr"],
  ["hr-settings", "/hr/settings", "hr"],
  ["hr-teams", "/hr/teams", "hr"],
  ["hr-report", "/hr/report", "hr"],
  ["calendar", "/calendar", "employee"],
  ["set-password", "/set-password?token=abc", "employee"],
  ["reset-password", "/reset-password?token=abc", "employee"],
  ["change-password", "/account/password", "employee"],
];

for (const [name, path, role] of SCREENS) {
  for (const width of [360, 1280]) {
    for (const theme of ["light", "dark"] as const) {
      test(`${name} @${width} ${theme}`, async ({ page }, info) => {
        const csp: string[] = [];
        page.on("console", (m) => /content security policy/i.test(m.text()) && csp.push(m.text()));
        await page.setViewportSize({ width, height: width === 360 ? 740 : 800 });
        await page.addInitScript((t) => localStorage.setItem("leavedesk-theme", t), theme);
        await mock(page, role);
        await page.goto(path);
        await page.locator("main h1").first().waitFor();
        await page.waitForLoadState("networkidle");
        expect(await page.evaluate(() => document.documentElement.dataset.theme)).toBe(theme);
        if (width === 360) {
          expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
        }
        const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
        expect(axe.violations.map((v) => `${v.id}: ${v.nodes[0]?.html.slice(0, 80)}`)).toEqual([]);
        expect(csp).toEqual([]);
        await page.screenshot({ path: info.outputPath(`${name}-${width}-${theme}.png`), fullPage: true });
      });
    }
  }
}

test("dashboard @1280 has three balance cards, then approvals and upcoming (5.3)", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await mock(page, "manager");
  await page.goto("/");
  await page.getByRole("heading", { name: "Awaiting your decision" }).waitFor();
  const grid = page.locator(".dash-grid > .card");
  await expect(grid).toHaveCount(3);
  const row = page.locator(".dash-row > .card");
  await expect(row).toHaveCount(2);
  const [a, b] = await Promise.all([grid.first().boundingBox(), row.first().boundingBox()]);
  expect(b!.y).toBeGreaterThan(a!.y + a!.height - 1);
  const cols = await page.locator(".dash-grid").evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(" ").length);
  expect(cols).toBe(3);
});

test("employee dashboard makes no /approvals call", async ({ page }) => {
  const calls: string[] = [];
  page.on("request", (r) => calls.push(r.url()));
  await mock(page, "employee");
  await page.goto("/");
  await page.getByRole("heading", { name: "Upcoming leave" }).waitFor();
  expect(calls.some((c) => c.includes("/approvals"))).toBe(false);
});

test("bottom tab bar replaces top tabs below 768 px with 44 px targets", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await mock(page, "manager");
  await page.goto("/");
  await page.getByRole("navigation", { name: "Main, bottom" }).waitFor();
  await expect(page.getByRole("navigation", { name: "Main", exact: true })).toBeHidden();
  const boxes = await page.locator(".bottombar a").evaluateAll((els) => els.map((e) => e.getBoundingClientRect().height));
  expect(Math.min(...boxes)).toBeGreaterThanOrEqual(44);
});
