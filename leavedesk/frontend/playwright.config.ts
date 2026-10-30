import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8000",
    viewport: { width: 360, height: 640 },
    // Optional: a preinstalled Chromium when the pinned Playwright browser is not downloaded.
    launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined },
  },
});
