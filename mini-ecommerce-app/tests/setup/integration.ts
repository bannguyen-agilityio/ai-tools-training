import './test-env';
import { prisma, configureSqlite } from '../../src/config/prisma';

beforeAll(async () => {
  await configureSqlite();
});

afterAll(async () => {
  await prisma.$disconnect();
});
