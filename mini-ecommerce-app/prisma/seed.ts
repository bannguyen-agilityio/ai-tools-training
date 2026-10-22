/**
 * Seed script: creates the two demo accounts and a small catalogue.
 * Run with `npm run prisma:seed`.
 */
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

const ADMIN_EMAIL = 'admin@shop.local';
const CUSTOMER_EMAIL = 'customer@shop.local';
const DEMO_PASSWORD = 'Password123!';

const products = [
  { sku: 'TSHIRT-BLK-M', name: 'Classic T-Shirt (Black, M)', description: 'Cotton crew neck, unisex fit.', priceCents: 2500, stock: 40 },
  { sku: 'TSHIRT-BLK-L', name: 'Classic T-Shirt (Black, L)', description: 'Cotton crew neck, unisex fit.', priceCents: 2500, stock: 25 },
  { sku: 'TSHIRT-WHT-S', name: 'Classic T-Shirt (White, S)', description: 'Cotton crew neck, unisex fit.', priceCents: 2500, stock: 12 },
  { sku: 'HOODIE-GRY-M', name: 'Fleece Hoodie (Grey, M)', description: 'Heavyweight fleece, kangaroo pocket.', priceCents: 6500, stock: 18 },
  { sku: 'HOODIE-NVY-XL', name: 'Fleece Hoodie (Navy, XL)', description: 'Heavyweight fleece, kangaroo pocket.', priceCents: 6500, stock: 8 },
  { sku: 'MUG-CERAMIC', name: 'Ceramic Mug 350ml', description: 'Dishwasher and microwave safe.', priceCents: 1800, stock: 120 },
  { sku: 'MUG-STUDIO', name: 'Studio Mug 400ml', description: 'Double-wall insulated.', priceCents: 3200, stock: 60 },
  { sku: 'MOUSE-WIRELESS', name: 'Wireless Mouse', description: 'Silent clicks, USB-C receiver.', priceCents: 4500, stock: 30 },
  { sku: 'MOUSE-GAMING', name: 'Gaming Mouse RGB', description: '16000 DPI, 7 programmable buttons.', priceCents: 7900, stock: 15 },
  { sku: 'KBD-MECH-87', name: 'Mechanical Keyboard 87 keys', description: 'Hot-swappable, brown switches.', priceCents: 12900, stock: 9 },
  { sku: 'CABLE-USBC-2M', name: 'USB-C Cable 2m', description: '100W charging, braided.', priceCents: 1500, stock: 200 },
  { sku: 'STAND-DESK', name: 'Laptop Stand (aluminium)', description: 'Adjustable height, foldable.', priceCents: 5900, stock: 3 },
  { sku: 'BOOK-SQL', name: 'Designing Data-Intensive Applications', description: 'Paperback, 2nd edition.', priceCents: 4900, stock: 0 },
  { sku: 'LAMP-LED', name: 'LED Desk Lamp', description: 'Dimmable, 3 colour temperatures.', priceCents: 5400, stock: 22 },
  { sku: 'BAG-CANVAS', name: 'Canvas Tote Bag', description: 'Heavy cotton, inner pocket.', priceCents: 2200, stock: 47 },
];

async function main(): Promise<void> {
  const passwordHash = await bcrypt.hash(DEMO_PASSWORD, 12);

  const admin = await prisma.user.upsert({
    where: { email: ADMIN_EMAIL },
    update: { name: 'Admin', role: 'ADMIN', passwordHash },
    create: { email: ADMIN_EMAIL, name: 'Admin', role: 'ADMIN', passwordHash },
  });

  const customer = await prisma.user.upsert({
    where: { email: CUSTOMER_EMAIL },
    update: { name: 'Customer', role: 'CUSTOMER', passwordHash },
    create: { email: CUSTOMER_EMAIL, name: 'Customer', role: 'CUSTOMER', passwordHash },
  });

  for (const product of products) {
    await prisma.product.upsert({
      where: { sku: product.sku },
      update: {
        name: product.name,
        description: product.description,
        priceCents: product.priceCents,
        stock: product.stock,
        active: true,
      },
      create: { ...product, active: true },
    });
  }

  console.log('Seed complete:');
  console.log(`  admin    ${admin.email} / ${DEMO_PASSWORD}`);
  console.log(`  customer ${customer.email} / ${DEMO_PASSWORD}`);
  console.log(`  ${products.length} products`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
