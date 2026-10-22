import { Router } from 'express';
import { authenticate } from '../../middleware/auth';
import { createLoginRateLimiter } from '../../middleware/rate-limit';
import { validateBody } from '../../middleware/validate';
import { login, me, register } from './auth.controller';
import { loginSchema, registerSchema } from './auth.schemas';

export function createAuthRouter(): Router {
  const router = Router();

  router.post('/auth/register', validateBody(registerSchema), register);
  router.post('/auth/login', createLoginRateLimiter(), validateBody(loginSchema), login);
  router.get('/auth/me', authenticate, me);

  return router;
}
