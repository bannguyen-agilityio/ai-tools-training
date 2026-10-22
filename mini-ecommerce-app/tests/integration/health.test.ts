import request from 'supertest';
import { createApp } from '../../src/app';

const app = createApp();

describe('GET /api/v1/health', () => {
  it('reports the process as alive', async () => {
    const response = await request(app).get('/api/v1/health');

    expect(response.status).toBe(200);
    expect(response.body).toMatchObject({
      success: true,
      data: { status: 'ok' },
    });
  });

  it('exposes uptime', async () => {
    const response = await request(app).get('/api/v1/health');

    expect(typeof response.body.data.uptime).toBe('number');
  });
});

describe('GET /api/v1/health/ready', () => {
  it('confirms the database is reachable', async () => {
    const response = await request(app).get('/api/v1/health/ready');

    expect(response.status).toBe(200);
    expect(response.body).toMatchObject({
      success: true,
      data: { status: 'ready', database: 'up' },
    });
  });
});
