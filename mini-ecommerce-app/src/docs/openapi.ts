import type { OpenAPIV3 } from 'openapi-types';

const openapi: OpenAPIV3.Document = {
  openapi: '3.1.0',
  info: {
    title: 'Mini E-commerce REST API',
    description: 'Mini e-commerce REST API built with Node.js, Express, TypeScript, Prisma, SQLite, and Zod.',
    version: '1.0.0',
    contact: {
      name: 'API Support',
    },
    license: {
      name: 'MIT',
    },
  },
  servers: [
    {
      url: '/api/v1',
      description: 'Current server (same origin as this page)',
    },
  ],
  tags: [
    { name: 'Health', description: 'Liveness and readiness probes' },
    { name: 'Auth', description: 'Authentication endpoints' },
    { name: 'Users', description: 'User profile' },
    { name: 'Products', description: 'Product catalog' },
    { name: 'Cart', description: 'Shopping cart' },
    { name: 'Orders', description: 'Orders and checkout' },
  ],
  components: {
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        description: 'Enter JWT token obtained from /auth/login',
      },
    },
    schemas: {
      SuccessResponse: {
        type: 'object',
        required: ['success', 'data'],
        properties: {
          success: { type: 'boolean', enum: [true] },
          data: { type: 'object' },
          meta: { type: 'object' },
        },
      },
      ErrorResponse: {
        type: 'object',
        required: ['success', 'error'],
        properties: {
          success: { type: 'boolean', enum: [false] },
          error: {
            type: 'object',
            required: ['code', 'message'],
            properties: {
              code: { type: 'string' },
              message: { type: 'string' },
              details: { type: 'array', items: { type: 'object' } },
            },
          },
          requestId: { type: 'string' },
        },
      },
      PaginationMeta: {
        type: 'object',
        required: ['page', 'limit', 'total', 'totalPages', 'hasNext', 'hasPrev'],
        properties: {
          page: { type: 'integer' },
          limit: { type: 'integer' },
          total: { type: 'integer' },
          totalPages: { type: 'integer' },
          hasNext: { type: 'boolean' },
          hasPrev: { type: 'boolean' },
        },
      },
      User: {
        type: 'object',
        required: ['id', 'email', 'name', 'role', 'createdAt'],
        properties: {
          id: { type: 'string' },
          email: { type: 'string', format: 'email' },
          name: { type: 'string' },
          role: { type: 'string', enum: ['CUSTOMER', 'ADMIN'] },
          createdAt: { type: 'string', format: 'date-time' },
        },
      },
      AuthResult: {
        type: 'object',
        required: ['user', 'accessToken', 'tokenType'],
        properties: {
          user: { $ref: '#/components/schemas/User' },
          accessToken: { type: 'string', description: 'JWT signed with HS256' },
          tokenType: { type: 'string', enum: ['Bearer'] },
        },
      },
      RegisterRequest: {
        type: 'object',
        required: ['email', 'password', 'name'],
        properties: {
          email: { type: 'string', format: 'email' },
          password: { type: 'string', minLength: 8, description: 'At most 72 bytes (bcrypt limit)' },
          name: { type: 'string', minLength: 1, maxLength: 100 },
        },
      },
      LoginRequest: {
        type: 'object',
        required: ['email', 'password'],
        properties: {
          email: { type: 'string', format: 'email' },
          password: { type: 'string' },
        },
      },
      Health: {
        type: 'object',
        required: ['status'],
        properties: {
          status: { type: 'string', enum: ['ok'] },
          uptime: { type: 'number' },
        },
      },
      Ready: {
        type: 'object',
        required: ['status', 'database'],
        properties: {
          status: { type: 'string', enum: ['ready'] },
          database: { type: 'string', enum: ['up'] },
        },
      },
    },
    responses: {
      Unauthorized: {
        description: 'Unauthorized',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/ErrorResponse' },
            example: {
              success: false,
              error: { code: 'UNAUTHORIZED', message: 'Authentication required' },
              requestId: 'req_123',
            },
          },
        },
      },
      Forbidden: {
        description: 'Forbidden',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/ErrorResponse' },
            example: {
              success: false,
              error: { code: 'FORBIDDEN', message: 'You do not have permission to perform this action' },
              requestId: 'req_123',
            },
          },
        },
      },
      NotFound: {
        description: 'Not Found',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/ErrorResponse' },
            example: {
              success: false,
              error: { code: 'NOT_FOUND', message: 'Resource not found' },
              requestId: 'req_123',
            },
          },
        },
      },
      ValidationError: {
        description: 'Validation Error',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/ErrorResponse' },
            example: {
              success: false,
              error: {
                code: 'VALIDATION_ERROR',
                message: 'Request validation failed',
                details: [{ path: 'email', message: 'Invalid email' }],
              },
              requestId: 'req_123',
            },
          },
        },
      },
      RateLimited: {
        description: 'Too Many Requests',
        content: {
          'application/json': {
            schema: { $ref: '#/components/schemas/ErrorResponse' },
            example: {
              success: false,
              error: { code: 'RATE_LIMITED', message: 'Too many requests, please try again later' },
              requestId: 'req_123',
            },
          },
        },
      },
    },
  },
  paths: {
    '/auth/register': {
      post: {
        tags: ['Auth'],
        summary: 'Register a new account',
        description: 'Always creates a CUSTOMER account. Returns a JWT so the client is signed in immediately.',
        requestBody: {
          required: true,
          content: { 'application/json': { schema: { $ref: '#/components/schemas/RegisterRequest' } } },
        },
        responses: {
          '201': {
            description: 'Account created',
            content: {
              'application/json': {
                schema: {
                  allOf: [
                    { $ref: '#/components/schemas/SuccessResponse' },
                    { type: 'object', properties: { data: { $ref: '#/components/schemas/AuthResult' } } },
                  ],
                },
              },
            },
          },
          '400': { $ref: '#/components/responses/ValidationError' },
          '409': {
            description: 'Email already registered (EMAIL_TAKEN)',
            content: { 'application/json': { schema: { $ref: '#/components/schemas/ErrorResponse' } } },
          },
        },
      },
    },
    '/auth/login': {
      post: {
        tags: ['Auth'],
        summary: 'Log in',
        description:
          'Rate-limited per IP (LOGIN_RATE_LIMIT_MAX attempts per LOGIN_RATE_LIMIT_WINDOW_MS). Exceeding it returns 429 with a Retry-After header.',
        requestBody: {
          required: true,
          content: { 'application/json': { schema: { $ref: '#/components/schemas/LoginRequest' } } },
        },
        responses: {
          '200': {
            description: 'Authenticated',
            content: {
              'application/json': {
                schema: {
                  allOf: [
                    { $ref: '#/components/schemas/SuccessResponse' },
                    { type: 'object', properties: { data: { $ref: '#/components/schemas/AuthResult' } } },
                  ],
                },
              },
            },
          },
          '400': { $ref: '#/components/responses/ValidationError' },
          '401': { $ref: '#/components/responses/Unauthorized' },
          '429': { $ref: '#/components/responses/RateLimited' },
        },
      },
    },
    '/auth/me': {
      get: {
        tags: ['Auth'],
        summary: 'Current user',
        security: [{ bearerAuth: [] }],
        responses: {
          '200': {
            description: 'Current user',
            content: {
              'application/json': {
                schema: {
                  allOf: [
                    { $ref: '#/components/schemas/SuccessResponse' },
                    { type: 'object', properties: { data: { $ref: '#/components/schemas/User' } } },
                  ],
                },
              },
            },
          },
          '401': { $ref: '#/components/responses/Unauthorized' },
        },
      },
    },
    '/health': {
      get: {
        tags: ['Health'],
        summary: 'Liveness probe',
        description: 'Returns 200 if the process is alive. Does not check the database.',
        responses: {
          '200': {
            description: 'OK',
            content: {
              'application/json': {
                schema: {
                  allOf: [
                    { $ref: '#/components/schemas/SuccessResponse' },
                    {
                      type: 'object',
                      properties: {
                        data: { $ref: '#/components/schemas/Health' },
                      },
                    },
                  ],
                },
                example: { success: true, data: { status: 'ok', uptime: 123.45 } },
              },
            },
          },
        },
      },
    },
    '/health/ready': {
      get: {
        tags: ['Health'],
        summary: 'Readiness probe',
        description: 'Returns 200 if the process is alive and the database is reachable.',
        responses: {
          '200': {
            description: 'OK',
            content: {
              'application/json': {
                schema: {
                  allOf: [
                    { $ref: '#/components/schemas/SuccessResponse' },
                    {
                      type: 'object',
                      properties: {
                        data: { $ref: '#/components/schemas/Ready' },
                      },
                    },
                  ],
                },
                example: { success: true, data: { status: 'ready', database: 'up' } },
              },
            },
          },
          '500': {
            description: 'Database unreachable',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/ErrorResponse' },
                example: {
                  success: false,
                  error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' },
                  requestId: 'req_123',
                },
              },
            },
          },
        },
      },
    },
  },
};

export function buildOpenApiDocument(): OpenAPIV3.Document {
  return openapi;
}
