import bcrypt from 'bcryptjs';
import type { Role, User } from '@prisma/client';
import { env } from '../../config/env';
import { EmailTakenError, UnauthorizedError } from '../../core/errors';
import { authRepository, isUniqueViolation } from './auth.repository';
import type { LoginInput, RegisterInput } from './auth.schemas';
import { signAccessToken } from './token';

export interface PublicUser {
  id: string;
  email: string;
  name: string;
  role: Role;
  createdAt: Date;
}

export interface AuthResult {
  user: PublicUser;
  accessToken: string;
  tokenType: 'Bearer';
}

export function toPublicUser(user: User): PublicUser {
  return { id: user.id, email: user.email, name: user.name, role: user.role, createdAt: user.createdAt };
}

// Compared against when the email is unknown so login timing does not reveal which emails exist.
let dummyHash: Promise<string> | undefined;
const getDummyHash = (): Promise<string> => (dummyHash ??= bcrypt.hash('not-a-real-password', env.BCRYPT_ROUNDS));

function issueToken(user: User): AuthResult {
  return {
    user: toPublicUser(user),
    accessToken: signAccessToken({ sub: user.id, role: user.role }),
    tokenType: 'Bearer',
  };
}

export const authService = {
  /** Public registration always creates a CUSTOMER; admins are provisioned out of band (seed). */
  async register(input: RegisterInput): Promise<AuthResult> {
    if (await authRepository.findByEmail(input.email)) throw new EmailTakenError();

    const passwordHash = await bcrypt.hash(input.password, env.BCRYPT_ROUNDS);
    try {
      const user = await authRepository.create({
        email: input.email,
        passwordHash,
        name: input.name,
        role: 'CUSTOMER',
      });
      return issueToken(user);
    } catch (error) {
      // Lost a race with a concurrent registration of the same email.
      if (isUniqueViolation(error)) throw new EmailTakenError();
      throw error;
    }
  },

  async login(input: LoginInput): Promise<AuthResult> {
    const user = await authRepository.findByEmail(input.email);
    const matches = await bcrypt.compare(input.password, user?.passwordHash ?? (await getDummyHash()));
    if (!user || !matches) throw new UnauthorizedError('Invalid email or password');
    return issueToken(user);
  },

  async me(userId: string): Promise<PublicUser> {
    const user = await authRepository.findById(userId);
    if (!user) throw new UnauthorizedError('Account no longer exists');
    return toPublicUser(user);
  },
};
