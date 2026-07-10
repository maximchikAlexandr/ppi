/**
 * useLatestRequest: monotonically-tagged async state.
 *
 * Returns a function `run` that, when called, increments a generation
 * counter; only the result of the latest call is committed to state.
 * Stale promises (older generation) are silently dropped — the typical
 * "click button, switch tab, last result wins" pattern.
 *
 * State is `RemoteData<T, E>`. Default error type is `string`; pages
 * that need typed pipeline errors pass a custom error type.
 */
import { useCallback, useRef, useState } from "react";

import { type RemoteData, idle, loading, success, failure } from "./remoteData";

export type UseLatestRequestResult<T, E = string> = {
  readonly state: RemoteData<T, E>;
  readonly run: (promise: Promise<T>) => Promise<void>;
  readonly reset: () => void;
  readonly generation: number;
};

export function useLatestRequest<T, E = string>(
  initial: RemoteData<T, E> = idle<T, E>(),
): UseLatestRequestResult<T, E> {
  const [state, setState] = useState<RemoteData<T, E>>(initial);
  const generationRef = useRef(0);

  const run = useCallback(async (promise: Promise<T>) => {
    const generation = generationRef.current + 1;
    generationRef.current = generation;
    setState(loading<T, E>());
    try {
      const data = await promise;
      if (generationRef.current === generation) {
        setState(success<T, E>(data));
      }
    } catch (err: unknown) {
      if (generationRef.current === generation) {
        setState(failure<T, E>(err as E));
      }
    }
  }, []);

  const reset = useCallback(() => {
    generationRef.current += 1;
    setState(idle<T, E>());
  }, []);

  return { state, run, reset, generation: generationRef.current };
}
