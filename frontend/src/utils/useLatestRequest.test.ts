import { describe, it, expect, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useLatestRequest } from "./useLatestRequest";
import { idle, loading, success, failure } from "./remoteData";

function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("useLatestRequest", () => {
  it("starts in the supplied initial state", () => {
    const { result } = renderHook(() => useLatestRequest(idle()));
    expect(result.current.state).toEqual({ status: "idle" });
  });

  it("transitions to success when the promise resolves", async () => {
    const { result } = renderHook(() => useLatestRequest<string>());
    const p = Promise.resolve("data");
    await act(async () => {
      await result.current.run(p);
    });
    expect(result.current.state).toEqual({ status: "success", data: "data" });
  });

  it("transitions to error when the promise rejects", async () => {
    const { result } = renderHook(() => useLatestRequest<string, Error>());
    const p = Promise.reject(new Error("boom"));
    await act(async () => {
      await result.current.run(p);
    });
    expect(result.current.state.status).toBe("error");
    if (result.current.state.status === "error") {
      expect((result.current.state.error as Error).message).toBe("boom");
    }
  });

  it("discards stale results: a later call's loading is what wins", async () => {
    const { result } = renderHook(() => useLatestRequest<string>());
    const d1 = deferred<string>();
    const d2 = deferred<string>();
    act(() => {
      result.current.run(d1.promise);
    });
    expect(result.current.state).toEqual({ status: "loading" });
    act(() => {
      result.current.run(d2.promise);
    });
    expect(result.current.state).toEqual({ status: "loading" });
    await act(async () => {
      d1.resolve("stale");
      d2.resolve("fresh");
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.state).toEqual({ status: "success", data: "fresh" });
  });

  it("discards stale errors", async () => {
    const { result } = renderHook(() => useLatestRequest<string, Error>());
    const d1 = deferred<string>();
    const d2 = deferred<string>();
    act(() => {
      result.current.run(d1.promise);
    });
    act(() => {
      result.current.run(d2.promise);
    });
    await act(async () => {
      d1.reject(new Error("stale"));
      d2.resolve("ok");
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.state).toEqual({ status: "success", data: "ok" });
  });

  it("reset bumps the generation and clears the state", () => {
    const { result } = renderHook(() => useLatestRequest<string>());
    act(() => {
      result.current.run(Promise.resolve("x"));
    });
    const before = result.current.generation;
    act(() => {
      result.current.reset();
    });
    expect(result.current.generation).toBeGreaterThan(before);
    expect(result.current.state).toEqual({ status: "idle" });
  });
});

describe("RemoteData helpers", () => {
  it("constructs the right variant", () => {
    expect(idle()).toEqual({ status: "idle" });
    expect(loading()).toEqual({ status: "loading" });
    expect(success(42)).toEqual({ status: "success", data: 42 });
    expect(failure("err")).toEqual({ status: "error", error: "err" });
  });
});
