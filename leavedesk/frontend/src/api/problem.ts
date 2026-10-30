export interface FieldError {
  field: string;
  message: string;
}

/** Normalised API error from the spec 6.1 envelope. */
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
    details?: { field?: string; issue?: string }[];
  };
}

export async function parseProblem(res: Response): Promise<ApiError> {
  let body: Envelope = {};
  try {
    body = (await res.json()) as Envelope;
  } catch {
    // Non-JSON body: fall back to the status text.
  }
  const fields = (body.error?.details ?? []).flatMap((d) =>
    d.field && d.issue ? [{ field: d.field, message: d.issue }] : [],
  );
  return new ApiError(res.status, body.error?.message ?? res.statusText ?? "Request failed", body.error?.code, fields);
}
