/**
 * Adapter: /api/v1 ErrorResponse DTO -> generic Error.
 */
export class GenericApiError extends Error {
  code: string;
  details: unknown;
  requestId: string | null;
  status: number;

  constructor(opts: {
    code: string;
    message: string;
    details?: unknown;
    requestId?: string | null;
    status: number;
  }) {
    super(opts.message);
    this.code = opts.code;
    this.details = opts.details ?? null;
    this.requestId = opts.requestId ?? null;
    this.status = opts.status;
  }
}

export function adaptError(
  status: number,
  body: unknown,
): GenericApiError {
  if (body && typeof body === "object" && "error" in body) {
    const e = (body as { error: { code?: string; message?: string; details?: unknown; requestId?: string | null } }).error;
    return new GenericApiError({
      code: e.code ?? "HTTP_ERROR",
      message: e.message ?? `HTTP ${status}`,
      details: e.details ?? null,
      requestId: e.requestId ?? null,
      status,
    });
  }
  return new GenericApiError({
    code: "HTTP_ERROR",
    message: `HTTP ${status}`,
    status,
  });
}
