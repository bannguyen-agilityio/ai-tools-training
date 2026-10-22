import { prisma } from '../../src/config/prisma';

/**
 * Empties every table. Children first so foreign keys stay satisfied.
 * Called before each integration test so suites never influence each other.
 */
export async function resetDatabase(): Promise<void> {
  await prisma.stockMovement.deleteMany();
  await prisma.orderItem.deleteMany();
  await prisma.order.deleteMany();
  await prisma.cartItem.deleteMany();
  await prisma.cart.deleteMany();
  await prisma.product.deleteMany();
  await prisma.user.deleteMany();
}
