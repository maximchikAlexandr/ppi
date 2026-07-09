import { describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useDrilldownStack } from "./useDrilldownStack";

describe("useDrilldownStack", () => {
  it("pushes, pops, and clears frames", () => {
    const { result } = renderHook(() => useDrilldownStack());
    expect(result.current.top).toBeNull();
    act(() => {
      result.current.push({ tableId: "a", title: "A", params: {} });
    });
    expect(result.current.top?.tableId).toBe("a");
    act(() => {
      result.current.push({ tableId: "b", title: "B", params: { x: 1 } });
    });
    expect(result.current.top?.tableId).toBe("b");
    expect(result.current.stack).toHaveLength(2);
    act(() => {
      result.current.pop();
    });
    expect(result.current.top?.tableId).toBe("a");
    act(() => {
      result.current.clear();
    });
    expect(result.current.stack).toEqual([]);
  });
});
