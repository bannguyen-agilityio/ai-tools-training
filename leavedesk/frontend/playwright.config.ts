import { defineConfig } from "@playwright/test";

// Desktop projects for the feature suite (e2e/features); the 360 px R31 checks stay in e2e/a11y.spec.ts.
const launchOptions = { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined };

export default defineConfig({
  testDir: "e2e",
  workers: 1, // one shared database; tests reseed it
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8000", launchOptions },
  projects: [
    { name: "mobile-360", testMatch: /a11y\.spec\.ts/, use: { viewport: { width: 360, height: 640 } } },
    { name: "desktop-1280", testDir: "e2e/features", use: { viewport: { width: 1280, height: 800 } } },
    { name: "desktop-1024", testDir: "e2e/features", use: { viewport: { width: 1024, height: 768 } } },
  ],
});
