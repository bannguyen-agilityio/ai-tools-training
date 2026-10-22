import swaggerUi from 'swagger-ui-express';
import type { Express } from 'express';
import { buildOpenApiDocument } from './openapi';

export function setupDocs(app: Express): void {
  const spec = buildOpenApiDocument();

  // Serve the raw spec
  app.get('/api/v1/docs.json', (_req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.send(spec);
  });
  // Also expose at root-level common paths for convenience
  app.get('/docs.json', (_req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.send(spec);
  });

  // Swagger UI
  app.use(
    '/api/v1/docs',
    swaggerUi.serve,
    swaggerUi.setup(spec, {
      explorer: true,
      customSiteTitle: 'Mini E-commerce API Docs',
      swaggerOptions: {
        persistAuthorization: true,
      },
    }),
  );
  app.use(
    '/docs',
    swaggerUi.serve,
    swaggerUi.setup(spec, {
      explorer: true,
      customSiteTitle: 'Mini E-commerce API Docs',
      swaggerOptions: {
        persistAuthorization: true,
      },
    }),
  );
}
