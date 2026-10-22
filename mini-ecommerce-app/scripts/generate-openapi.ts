/**
 * Writes the OpenAPI document to `docs/openapi.json`.
 * The document itself is built in `src/docs/openapi.ts` (Stage 5).
 */
import { writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { buildOpenApiDocument } from '../src/docs/openapi';

const outputPath = path.resolve(__dirname, '..', 'docs', 'openapi.json');
mkdirSync(path.dirname(outputPath), { recursive: true });
writeFileSync(outputPath, `${JSON.stringify(buildOpenApiDocument(), null, 2)}\n`, 'utf8');
console.log(`OpenAPI document written to ${outputPath}`);
