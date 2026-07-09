/**
 * RemoteData<T> — typed async state for useLatestRequest and friends.
 *
 *   { status: "idle" }        -> not yet started
 *   { status: "loading" }     -> in flight (or stale, superseded)
 *   { status: "success", data } -> latest result
 *   { status: "error", error } -> latest failure
 *
 * Replaces ad-hoc pairs of (loadingX, error, generationRef) that every
 * page used to declare. A failed or stale request must be replaced
 * cleanly by the next one — see `useLatestRequest` for the contract.
 */
export type RemoteData<T, E = string> =
  | { readonly status: "idle" }
  | { readonly status: "loading" }
  | { readonly status: "success"; readonly data: T }
  | { readonly status: "error"; readonly error: E };

export const idle = <T, E = string>(): RemoteData<T, E> => ({ status: "idle" });
export const loading = <T, E = string>(): RemoteData<T, E> => ({ status: "loading" });
export const success = <T, E = string>(data: T): RemoteData<T, E> => ({
  status: "success",
  data,
});
export const failure = <T, E = string>(error: E): RemoteData<T, E> => ({
  status: "error",
  error,
});

export function isSuccess<T, E>(rd: RemoteData<T, E>): rd is { status: "success"; data: T } {
  return rd.status === "success";
}

export function isError<T, E>(rd: RemoteData<T, E>): rd is { status: "error"; error: E } {
  return rd.status === "error";
}
