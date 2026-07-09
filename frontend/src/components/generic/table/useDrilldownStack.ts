/**
 * Drilldown stack state and action execution helpers.
 */
import { useCallback, useState } from "react";

import type { DrilldownFrame } from "../../../domain/table";

export function useDrilldownStack() {
  const [stack, setStack] = useState<DrilldownFrame[]>([]);
  const push = useCallback((frame: DrilldownFrame) => {
    setStack((s) => [...s, frame]);
  }, []);
  const pop = useCallback(() => {
    setStack((s) => s.slice(0, -1));
  }, []);
  const clear = useCallback(() => {
    setStack([]);
  }, []);
  return { stack, push, pop, clear, top: stack[stack.length - 1] ?? null };
}
