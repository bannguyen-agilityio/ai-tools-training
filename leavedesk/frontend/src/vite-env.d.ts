/// <reference types="vite/client" />
import "vitest";
import type { AxeMatchers } from "vitest-axe/matchers";

declare module "vitest" {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type -- augmentation merges matchers
  interface Assertion extends AxeMatchers {}
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type -- augmentation merges matchers
  interface AsymmetricMatchersContaining extends AxeMatchers {}
}
