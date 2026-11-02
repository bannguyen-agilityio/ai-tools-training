import { z } from "zod";

/** Mirrors `MIN_LENGTH` in app/modules/auth/passwords.py (R2); the server stays the authority. */
export const PASSWORD_MIN = 12;

export const newPassword = z
  .string()
  .min(PASSWORD_MIN, `Use at least ${PASSWORD_MIN} characters.`)
  .max(256, "Use at most 256 characters.");
