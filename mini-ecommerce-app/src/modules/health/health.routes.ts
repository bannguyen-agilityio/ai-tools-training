import { Router } from 'express';
import { prisma } from '../../config/prisma';
import { sendSuccess } from '../../core/response';

export const healthRouter = Router();

/** Liveness: the process is up. Does not touch the database. */
healthRouter.get('/health', (_req, res) => {
  sendSuccess(res, { status: 'ok', uptime: process.uptime() });
});

/** Readiness: the process is up *and* the database answers. */
healthRouter.get('/health/ready', async (_req, res) => {
  await prisma.$queryRaw`SELECT 1`;
  sendSuccess(res, { status: 'ready', database: 'up' });
});
