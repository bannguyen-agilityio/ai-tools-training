import { expect, test, type Page } from "@playwright/test";
import { outbox, requestLeave, reseed, signIn, sql, workday, type Persona } from "../support";

test.beforeEach(() => reseed());

/** emp1 submits leave for workday(n); returns the request id. */
async function submitAs(page: Page, who: Persona, n = 8, type?: "Annual" | "Sick"): Promise<string> {
  await signIn(page, who);
  await requestLeave(page, { start: workday(n), type });
  await page.waitForURL(/\/requests\/[0-9a-f-]+$/);
  return page.url().split("/").pop()!;
}
const status = (id: string) => sql<{ status: string }>(`select status from leave_request where id='${id}'`)[0].status;

test.describe("Approvals (R17-R22)", () => {
  test("E2E-APR-1/2: manager sees the request with the name and approves it", async ({ page, browser }) => {
    const id = await submitAs(page, "emp1");
    const ctx = await browser.newContext();
    const m = await ctx.newPage();
    await signIn(m, "mgr1");
    await m.goto("/approvals");
    await expect(m.getByText("Eli Employee")).toBeVisible();
    await m.getByRole("button", { name: "Approve" }).click();
    await expect(m.getByText("Request approved.")).toBeVisible();
    expect(status(id)).toBe("approved");
    expect(outbox("emp1@asnet.com.vn").map((e) => e.template)).toContain("request_approved");
    await ctx.close();
  });

  test("E2E-APR-3/4: reject needs a reason, then the employee sees it", async ({ page, browser }) => {
    const id = await submitAs(page, "emp1");
    const ctx = await browser.newContext();
    const m = await ctx.newPage();
    await signIn(m, "mgr1");
    await m.goto("/approvals");
    await m.getByRole("button", { name: "Reject" }).click();
    await m.getByRole("form", { name: "Reject request" }).getByRole("button", { name: /^Reject/ }).click();
    await expect(m.locator('[aria-invalid="true"]')).toBeFocused();
    expect(status(id)).toBe("pending");
    await m.getByLabel("Reason for rejecting").fill("Team is short that week");
    await m.getByRole("form", { name: "Reject request" }).getByRole("button", { name: /^Reject/ }).click();
    await expect(m.getByText("Request rejected.")).toBeVisible();
    expect(status(id)).toBe("rejected");
    await page.goto(`/requests/${id}`);
    await expect(page.getByText("Rejected", { exact: true })).toBeVisible();
    await ctx.close();
  });

  test("E2E-APR-6: decide from the request detail page", async ({ page, browser }) => {
    const id = await submitAs(page, "emp1");
    const ctx = await browser.newContext();
    const m = await ctx.newPage();
    await signIn(m, "mgr1");
    await m.goto(`/requests/${id}`);
    await m.getByRole("button", { name: "Approve" }).click();
    await expect.poll(() => status(id)).toBe("approved");
    await ctx.close();
  });

  test("E2E-APR-7/8: another team's manager and a plain employee cannot decide", async ({ page, browser }) => {
    const id = await submitAs(page, "emp1");
    const ctx = await browser.newContext();
    const other = await ctx.newPage();
    const csrf = await signIn(other, "mgr2");
    await other.goto("/approvals");
    await expect(other.getByText("Nothing is waiting for your decision.")).toBeVisible();
    const denied = await other.request.post(`/api/v1/approvals/${id}/approve`, {
      data: { version: 1 },
      headers: { "X-CSRF-Token": csrf },
    });
    expect(denied.status()).toBe(403);
    expect(status(id)).toBe("pending");
    const emp = await ctx.newPage();
    await signIn(emp, "emp3");
    await emp.goto("/");
    await expect(emp.getByRole("link", { name: "Approvals" })).toHaveCount(0);
    expect((await emp.request.get("/api/v1/approvals")).status()).toBe(403);
    await ctx.close();
  });

  test("E2E-APR-5: a second decision on the same request is refused", async ({ page, browser }) => {
    const id = await submitAs(page, "emp1");
    const ctx = await browser.newContext();
    const a = await ctx.newPage();
    const b = await ctx.newPage();
    const csrf = await signIn(a, "mgr1");
    await b.addInitScript((t) => sessionStorage.setItem("leavedesk.csrf", t), csrf); // same session, second tab
    await a.goto("/approvals");
    await b.goto("/approvals");
    await a.getByRole("button", { name: "Approve" }).click();
    await expect(a.getByText("Request approved.")).toBeVisible();
    await b.getByRole("button", { name: "Reject" }).click();
    await b.getByLabel("Reason for rejecting").fill("late");
    await b.getByRole("form", { name: "Reject request" }).getByRole("button", { name: /^Reject/ }).click();
    await expect(b.getByRole("alert")).toContainText(/already decided/i);
    expect(status(id)).toBe("approved");
    await ctx.close();
  });

  test("E2E-APR-11/12: manager request goes to HR; HR admin request goes to the deputy only", async ({ page, browser }) => {
    const mid = await submitAs(page, "mgr1");
    const ctx = await browser.newContext();
    const hr = await ctx.newPage();
    await signIn(hr, "hr2");
    await hr.goto("/approvals");
    await hr.getByRole("button", { name: "Approve" }).click();
    await expect.poll(() => status(mid)).toBe("approved");
    const p2 = await ctx.newPage();
    const hid = await submitAs(p2, "hr1", 20);
    await hr.goto("/approvals");
    await expect(hr.getByText("Nothing is waiting for your decision.")).toBeVisible();
    const dep = await ctx.newPage();
    await signIn(dep, "deputy");
    await dep.goto("/approvals");
    await dep.getByRole("button", { name: "Approve" }).click();
    await expect.poll(() => status(hid)).toBe("approved");
    await ctx.close();
  });

  test("E2E-APR-13: cover decision via On behalf of is audited and emails the direct manager", async ({ page, browser }) => {
    const id = await submitAs(page, "emp1");
    const ctx = await browser.newContext();
    const m2 = await ctx.newPage();
    await signIn(m2, "mgr2");
    await m2.goto("/approvals");
    await expect(m2.getByText("Eli Employee")).toHaveCount(0);
    await m2.getByRole("button", { name: "On behalf of" }).click();
    await expect(m2.getByText("Eli Employee")).toBeVisible();
    await m2.getByRole("button", { name: "Approve" }).click();
    await expect.poll(() => status(id)).toBe("approved");
    expect(sql(`select count(*)::int as n from audit_log where acting_for_id is not null`)[0]).toEqual({ n: 1 });
    expect(outbox("mgr1@asnet.com.vn").map((e) => e.template)).toContain("request_approved_on_behalf");
    await ctx.close();
  });

  test("E2E-APR-15: the Sick type is visible while deciding and Off afterwards", async ({ page, browser }) => {
    const id = await submitAs(page, "emp1", 1, "Sick");
    const ctx = await browser.newContext();
    const m = await ctx.newPage();
    await signIn(m, "mgr1");
    await m.goto("/approvals");
    await expect(m.getByText("Sick", { exact: true })).toBeVisible();
    await m.getByRole("button", { name: "Approve" }).click();
    await expect.poll(() => status(id)).toBe("approved");
    // After the decision the approver's own view of the request no longer names the type.
    await m.goto(`/requests/${id}`);
    await expect(m.getByText("Sick", { exact: true })).toHaveCount(0);
    await ctx.close();
  });

  test("E2E-APR-10: HR who entered a request cannot decide it", async ({ page }) => {
    const csrf = await signIn(page, "hr1");
    const emp = sql<{ id: string }>("select id from employee where email='mgr2@asnet.com.vn'")[0].id;
    const d = workday(8).toISOString().slice(0, 10);
    const made = await page.request.post("/api/v1/hr/requests", {
      data: { employee_id: emp, leave_type: "annual", start_date: d, end_date: d, start_part: "full", end_part: "full", entry_reason: "phone" },
      headers: { "X-CSRF-Token": csrf },
    });
    expect(made.status(), await made.text()).toBe(201);
    await page.goto("/approvals");
    await expect(page.getByText("Nothing is waiting for your decision.")).toBeVisible();
  });
});
