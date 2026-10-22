import './../setup/test-env';
import jwt from 'jsonwebtoken';
import { signAccessToken, verifyAccessToken } from '../../src/modules/auth/token';
import { UnauthorizedError } from '../../src/core/errors';
import { TEST_JWT_SECRET } from '../helpers/constants';

describe('access tokens', () => {
  it('signs HS256 tokens that round-trip subject and role', () => {
    const token = signAccessToken({ sub: 'user-1', role: 'ADMIN' });

    expect(jwt.decode(token, { complete: true })?.header.alg).toBe('HS256');
    expect(verifyAccessToken(token)).toMatchObject({ sub: 'user-1', role: 'ADMIN' });
  });

  it('rejects a token signed with another secret', () => {
    const token = jwt.sign({ role: 'ADMIN' }, 'x'.repeat(40), { subject: 'u' });
    expect(() => verifyAccessToken(token)).toThrow(UnauthorizedError);
  });

  it('rejects an unsigned (alg none) token', () => {
    const token = jwt.sign({ role: 'ADMIN' }, '', { algorithm: 'none', subject: 'u' });
    expect(() => verifyAccessToken(token)).toThrow(UnauthorizedError);
  });

  it('rejects other HMAC algorithms', () => {
    const token = jwt.sign({ role: 'ADMIN' }, TEST_JWT_SECRET, { algorithm: 'HS512', subject: 'u' });
    expect(() => verifyAccessToken(token)).toThrow(UnauthorizedError);
  });

  it('rejects expired tokens and unknown roles', () => {
    const expired = jwt.sign({ role: 'CUSTOMER' }, TEST_JWT_SECRET, { subject: 'u', expiresIn: -10 });
    const badRole = jwt.sign({ role: 'ROOT' }, TEST_JWT_SECRET, { subject: 'u' });
    expect(() => verifyAccessToken(expired)).toThrow(UnauthorizedError);
    expect(() => verifyAccessToken(badRole)).toThrow(UnauthorizedError);
  });
});
