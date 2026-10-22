describe('environment configuration', () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
    jest.resetModules();
  });

  it('fails fast when a required variable is invalid', async () => {
    // `dotenv` does not overwrite variables that already exist, so an empty
    // value survives the .env load and fails validation.
    process.env.DATABASE_URL = '';
    jest.resetModules();

    await expect(import('../../src/config/env')).rejects.toThrow(/DATABASE_URL/);
  });

  it('fails fast when the JWT secret is too short', async () => {
    process.env.JWT_SECRET = 'too-short';
    jest.resetModules();

    await expect(import('../../src/config/env')).rejects.toThrow(/JWT_SECRET/);
  });

  it('coerces numeric values and applies defaults', async () => {
    process.env.DATABASE_URL = 'file:./dev.db';
    process.env.JWT_SECRET = 'x'.repeat(40);
    delete process.env.PORT;
    delete process.env.BCRYPT_ROUNDS;
    delete process.env.NODE_ENV;
    jest.resetModules();

    const { env } = await import('../../src/config/env');

    expect(env.PORT).toBe(3000);
    expect(env.BCRYPT_ROUNDS).toBe(12);
    expect(env.NODE_ENV).toBe('development');
  });

  it('refuses to boot in production with the example secret', async () => {
    process.env.NODE_ENV = 'production';
    process.env.DATABASE_URL = 'file:./dev.db';
    process.env.JWT_SECRET = 'change-me-to-a-long-random-string-at-least-32-chars';
    jest.resetModules();

    await expect(import('../../src/config/env')).rejects.toThrow(/JWT_SECRET/);
  });
});
