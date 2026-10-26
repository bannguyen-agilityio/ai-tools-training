import { z } from 'zod';

const email = z.string().trim().toLowerCase().pipe(z.email().max(254));

/** bcrypt only hashes the first 72 bytes, so longer passwords would be silently truncated. */
const password = z
  .string()
  .min(9, 'Password must be at least 9 characters')
  .refine((value) => Buffer.byteLength(value, 'utf8') <= 72, 'Password must be at most 72 bytes');

export const registerSchema = z.object({
  email,
  password,
  name: z.string().trim().min(1).max(100),
});

export const loginSchema = z.object({
  email,
  password: z.string().min(1).max(1024),
});

export type RegisterInput = z.infer<typeof registerSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
