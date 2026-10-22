import { Prisma, type Role, type User } from '@prisma/client';
import { prisma } from '../../config/prisma';

export const authRepository = {
  findByEmail(email: string): Promise<User | null> {
    return prisma.user.findUnique({ where: { email } });
  },

  findById(id: string): Promise<User | null> {
    return prisma.user.findUnique({ where: { id } });
  },

  create(data: { email: string; passwordHash: string; name: string; role?: Role }): Promise<User> {
    return prisma.user.create({ data });
  },
};

export function isUniqueViolation(error: unknown): boolean {
  return error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002';
}
