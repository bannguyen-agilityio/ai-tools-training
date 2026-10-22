import jwt, { type SignOptions } from 'jsonwebtoken';
import { Role } from '@prisma/client';
import { z } from 'zod';
import { env } from '../../config/env';
import { UnauthorizedError } from '../../core/errors';

const ALGORITHM = 'HS256';

const claimsSchema = z.object({
  sub: z.string().min(1),
  role: z.enum(Role),
});

export interface AuthClaims {
  sub: string;
  role: Role;
}

export function signAccessToken(claims: AuthClaims): string {
  return jwt.sign({ role: claims.role }, env.JWT_SECRET, {
    algorithm: ALGORITHM,
    subject: claims.sub,
    expiresIn: env.JWT_EXPIRES_IN as SignOptions['expiresIn'],
  });
}

/** Verifies signature (HS256 only, so `alg: none` and key-confusion tokens are rejected) and expiry. */
export function verifyAccessToken(token: string): AuthClaims {
  try {
    const payload = jwt.verify(token, env.JWT_SECRET, { algorithms: [ALGORITHM] });
    const claims = claimsSchema.safeParse(payload);
    if (!claims.success) throw new Error('malformed claims');
    return claims.data;
  } catch {
    throw new UnauthorizedError('Invalid or expired token');
  }
}
