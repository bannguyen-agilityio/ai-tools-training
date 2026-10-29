export interface FieldError {
  field: string;
  message: string;
}

/** Normalised API error. Understands the spec 6.1 envelope and RFC 9457 problem+json. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly code?: string,
    readonly fields: FieldError[] = [],
  ) {
    super(message);
  }
}

interface Envelope {
  error?: {
    code?: string;
    message?: string;
    details?: { field?: string; message?: string }[];
  };
  detail?: string;
  title?: string;
  errors?: { field?: string; message?: string }[];
}

function toFields(list: { field?: string; message?: string }[] = []): FieldError[] {
  return list.flatMap((d) => (d.field && d.message ? [{ field: d.field, message: d.message }] : []));
}

export async function parseProblem(res: Response): Promise<ApiError> {
  let body: Envelope = {};
  try {
    body = (await res.json()) as Envelope;
  } catch {
    // Non-JSON body: fall back to the status text.
  }
  const message = body.error?.message ?? body.detail ?? body.title ?? res.statusText ?? "Request failed";
  return new ApiError(res.status, message, body.error?.code, toFields(body.error?.details ?? body.errors));
}
