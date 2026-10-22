import request from 'supertest';
import { createApp } from '../../src/app';

const app = createApp();

describe('error envelope', () => {
  it('returns the standard 404 envelope for unknown routes', async () => {
    const response = await request(app).get('/api/v1/does-not-exist');

    expect(response.status).toBe(404);
    expect(response.body).toMatchObject({
      success: false,
      error: { code: 'NOT_FOUND' },
    });
    expect(response.body.error.message).toContain('/api/v1/does-not-exist');
  });

  it('returns a 400 envelope for malformed JSON bodies', async () => {
    const response = await request(app)
      .post('/api/v1/anything')
      .set('content-type', 'application/json')
      .send('{"broken":');

    expect(response.status).toBe(400);
    expect(response.body).toMatchObject({
      success: false,
      error: { code: 'VALIDATION_ERROR' },
    });
  });

  it('includes a request id in every error body and echoes it in the headers', async () => {
    const response = await request(app).get('/api/v1/nope').set('x-request-id', 'trace-me-123');

    expect(response.status).toBe(404);
    expect(response.body.requestId).toBe('trace-me-123');
    expect(response.headers['x-request-id']).toBe('trace-me-123');
  });

  it('generates a request id when the client does not supply one', async () => {
    const response = await request(app).get('/api/v1/nope');

    expect(response.body.requestId).toEqual(expect.any(String));
    expect(response.headers['x-request-id']).toBe(response.body.requestId);
  });

  it('does not leak internals of unexpected errors', async () => {
    const response = await request(app).get('/api/v1/nope');

    expect(response.body.error).not.toHaveProperty('stack');
    expect(response.body.error.message).not.toMatch(/at .*\.ts:\d+/);
  });
});
