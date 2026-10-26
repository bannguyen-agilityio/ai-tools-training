import request from 'supertest';
import bcrypt from 'bcryptjs';
import { createApp } from '../../src/app';
import { prisma } from '../../src/config/prisma';
import { requireRole, authenticate } from '../../src/middleware/auth';
import { signAccessToken } from '../../src/modules/auth/token';
import { resetDatabase } from '../helpers/database';
import express from 'express';
import { errorHandler } from '../../src/core/error-handler';

const credentials = { email: 'jane@example.com', password: 'Password123!', name: 'Jane' };

beforeEach(resetDatabase);

describe('POST /api/v1/auth/register', () => {
  it('creates a CUSTOMER, hashes with 12-round-format bcrypt, and returns a token without the hash', async () => {
    const res = await request(createApp()).post('/api/v1/auth/register').send(credentials);

    expect(res.status).toBe(201);
    expect(res.body.data.user).toMatchObject({ email: credentials.email, name: 'Jane', role: 'CUSTOMER' });
    expect(res.body.data.accessToken).toEqual(expect.any(String));
    expect(JSON.stringify(res.body)).not.toContain('passwordHash');

    const stored = await prisma.user.findUniqueOrThrow({ where: { email: credentials.email } });
    expect(stored.passwordHash).not.toContain(credentials.password);
    expect(await bcrypt.compare(credentials.password, stored.passwordHash)).toBe(true);
  });

  it('ignores a client-supplied role', async () => {
    const res = await request(createApp())
      .post('/api/v1/auth/register')
      .send({ ...credentials, role: 'ADMIN' });

    expect(res.status).toBe(201);
    expect(res.body.data.user.role).toBe('CUSTOMER');
  });

  it('normalises email case and rejects duplicates with EMAIL_TAKEN', async () => {
    const app = createApp();
    await request(app).post('/api/v1/auth/register').send(credentials);
    const res = await request(app)
      .post('/api/v1/auth/register')
      .send({ ...credentials, email: ' JANE@Example.com ' });

    expect(res.status).toBe(409);
    expect(res.body.error.code).toBe('EMAIL_TAKEN');
  });

  it.each([
    ['invalid email', { ...credentials, email: 'nope' }],
    ['short password', { ...credentials, password: 'short' }],
    ['password of 8 characters', { ...credentials, password: 'a'.repeat(8) }],
    ['password over 72 bytes', { ...credentials, password: 'a'.repeat(73) }],
    ['missing name', { email: credentials.email, password: credentials.password }],
  ])('rejects %s', async (_label, body) => {
    const res = await request(createApp()).post('/api/v1/auth/register').send(body);

    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('VALIDATION_ERROR');
  });

  it('requires at least 9 characters: rejects 8 with a clear message, accepts 9', async () => {
    const app = createApp();

    const tooShort = await request(app)
      .post('/api/v1/auth/register')
      .send({ ...credentials, password: 'a'.repeat(8) });
    expect(tooShort.status).toBe(400);
    expect(tooShort.body.error.details).toEqual([
      { path: 'password', message: 'Password must be at least 9 characters' },
    ]);

    const longEnough = await request(app)
      .post('/api/v1/auth/register')
      .send({ ...credentials, password: 'a'.repeat(9) });
    expect(longEnough.status).toBe(201);
  });
});

describe('POST /api/v1/auth/login', () => {
  it('returns a token that authenticates GET /auth/me', async () => {
    const app = createApp();
    await request(app).post('/api/v1/auth/register').send(credentials);

    const login = await request(app)
      .post('/api/v1/auth/login')
      .send({ email: 'JANE@example.com', password: credentials.password });
    expect(login.status).toBe(200);

    const me = await request(app).get('/api/v1/auth/me').set('Authorization', `Bearer ${login.body.data.accessToken}`);
    expect(me.status).toBe(200);
    expect(me.body.data).toMatchObject({ email: credentials.email, role: 'CUSTOMER' });
  });

  it('gives the same 401 for a wrong password and an unknown email', async () => {
    const app = createApp();
    await request(app).post('/api/v1/auth/register').send(credentials);

    const wrongPassword = await request(app)
      .post('/api/v1/auth/login')
      .send({ email: credentials.email, password: 'Wrong-pass1' });
    const unknownEmail = await request(app)
      .post('/api/v1/auth/login')
      .send({ email: 'ghost@example.com', password: 'Wrong-pass1' });

    for (const res of [wrongPassword, unknownEmail]) {
      expect(res.status).toBe(401);
      expect(res.body.error).toEqual({ code: 'UNAUTHORIZED', message: 'Invalid email or password' });
    }
  });

  it('rate-limits after LOGIN_RATE_LIMIT_MAX attempts with 429 and Retry-After', async () => {
    const app = createApp();
    const attempt = () =>
      request(app).post('/api/v1/auth/login').send({ email: credentials.email, password: 'Wrong-pass1' });

    for (let i = 0; i < 5; i++) expect((await attempt()).status).toBe(401);
    const limited = await attempt();

    expect(limited.status).toBe(429);
    expect(limited.body.error.code).toBe('RATE_LIMITED');
    expect(limited.headers['retry-after']).toBeDefined();
  });

  it('does not rate-limit registration', async () => {
    const app = createApp();
    for (let i = 0; i < 7; i++) {
      const res = await request(app)
        .post('/api/v1/auth/register')
        .send({ ...credentials, email: `u${i}@example.com` });
      expect(res.status).toBe(201);
    }
  });
});

describe('GET /api/v1/auth/me', () => {
  it.each([
    ['no header', undefined],
    ['wrong scheme', 'Basic abc'],
    ['garbage token', 'Bearer not.a.jwt'],
  ])('401 for %s', async (_label, header) => {
    const req = request(createApp()).get('/api/v1/auth/me');
    const res = await (header ? req.set('Authorization', header) : req);

    expect(res.status).toBe(401);
    expect(res.body.error.code).toBe('UNAUTHORIZED');
  });

  it('401 when the token is valid but the user was deleted', async () => {
    const token = signAccessToken({ sub: 'missing-user', role: 'CUSTOMER' });
    const res = await request(createApp()).get('/api/v1/auth/me').set('Authorization', `Bearer ${token}`);

    expect(res.status).toBe(401);
  });
});

describe('requireRole', () => {
  const app = express();
  app.get('/admin', authenticate, requireRole('ADMIN'), (_req, res) => void res.json({ ok: true }));
  app.use(errorHandler);

  it('allows ADMIN and forbids CUSTOMER with 403', async () => {
    const admin = signAccessToken({ sub: 'a', role: 'ADMIN' });
    const customer = signAccessToken({ sub: 'c', role: 'CUSTOMER' });

    expect((await request(app).get('/admin').set('Authorization', `Bearer ${admin}`)).status).toBe(200);
    const denied = await request(app).get('/admin').set('Authorization', `Bearer ${customer}`);
    expect(denied.status).toBe(403);
    expect(denied.body.error.code).toBe('FORBIDDEN');
  });
});
