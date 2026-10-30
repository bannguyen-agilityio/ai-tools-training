import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, type Page } from "@playwright/test";

export const PASSWORD = "Correct-Horse-Battery-9";
export type Persona = "hr1" | "hr2" | "deputy" | "mgr1" | "mgr2" | "emp1" | "emp2" | "emp3" | "orphan";
export const email = (p: Persona) => `${p}@asnet.com.vn`;

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const dbUrl = process.env.E2E_DATABASE_URL ?? "postgresql+psycopg://postgres:test@localhost:5434/leavedesk_e2e";

function db(...args: string[]): string {
  return execFileSync("uv", ["run", "python", "scripts/e2e_db.py", ...args], {
    cwd: root,
    env: { ...process.env, E2E_DATABASE_URL: dbUrl, PYTHONPATH: root },
    encoding: "utf8",
  });
}

/** Wipes people, requests, outbox and audit, and recreates the personas (see scripts/e2e_db.py). */
export const reseed = () => void db("seed");
export const sql = <T = Record<string, unknown>>(statement: string): T[] => JSON.parse(db("sql", statement));
export const outbox = (to: string) =>
  JSON.parse(db("outbox", to)) as { template: string; subject: string; body: string; status: string }[];

/** There is no sign-in screen yet, so sign in through the API and hand the SPA its CSRF token. */
export async function signIn(page: Page, who: Persona, password = PASSWORD): Promise<string> {
  const res = await page.request.post("/api/v1/auth/login", { data: { email: email(who), password } });
  expect(res.status(), await res.text()).toBe(200);
  const { csrf_token } = await res.json();
  await page.addInitScript((t) => sessionStorage.setItem("leavedesk.csrf", t), csrf_token);
  return csrf_token; // for direct page.request calls, which carry the cookie but not the header
}

const DAY = 24 * 3600 * 1000;
const fmt = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Ho_Chi_Minh" });
const iso = (d: Date) => d.toLocaleDateString("en-CA", { timeZone: "Asia/Ho_Chi_Minh" });
/** "Mon 2 Nov 2026", the format the date fields show and accept. */
export const label = (d: Date) => fmt.format(d).replace(",", "");

let holidays: Set<string> | undefined;
/** The n-th working day after today (Mon-Fri, not a seeded public holiday), n >= 1. */
export function workday(n: number): Date {
  holidays ??= new Set(sql<{ holiday_date: string }>("select holiday_date from public_holiday").map((h) => h.holiday_date));
  let d = new Date(iso(new Date()) + "T00:00:00Z");
  for (let left = n; left > 0; ) {
    d = new Date(d.getTime() + DAY);
    const wd = d.getUTCDay();
    if (wd !== 0 && wd !== 6 && !holidays.has(d.toISOString().slice(0, 10))) left--;
  }
  return d;
}

/** Fills and submits the Request leave form. Dates are Date values; single day when end omitted. */
export async function requestLeave(
  page: Page,
  o: { type?: "Annual" | "Sick" | "Unpaid"; start: Date; end?: Date; note?: string },
): Promise<void> {
  await page.goto("/requests/new");
  if (o.type) await page.getByLabel("Leave type").selectOption({ label: o.type });
  await page.getByLabel("Start date").fill(label(o.start));
  await page.getByLabel("End date").fill(label(o.end ?? o.start));
  if (o.note) await page.getByLabel("Note (optional)").fill(o.note);
  await page.getByRole("button", { name: "Submit request" }).click();
}
