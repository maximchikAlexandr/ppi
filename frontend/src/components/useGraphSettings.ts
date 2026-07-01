import { useCallback, useState } from "react";
import { useEffect } from "react";

import { loadSettingsFromStorage, trySaveSettings } from "./graphPersistence";
import {
  DEFAULT_FORCE_STATE,
  DEFAULT_FILTER_STATE,
  DEFAULT_GRAPH_SETTINGS,
  DEFAULT_SECTIONS_EXPANDED,
  type GraphDisplayState,
  type GraphFilterState,
  type GraphForceState,
  type GraphSectionKey,
  type GraphSettings,
} from "./graphSettingsTypes";

export function useGraphSettings(defaultEnabledEdgeKinds: Readonly<Record<string, boolean>> = {}) {
  const initial = loadSettingsFromStorage(defaultEnabledEdgeKinds);
  const [settings, setSettings] = useState<GraphSettings>(initial.settings);
  const [saveDisabled, setSaveDisabled] = useState(initial.saveDisabled);
  const [saveNotice, setSaveNotice] = useState<string | null>(
    initial.saveDisabled ? "Settings cannot be saved — browser storage is unavailable or full." : null,
  );

  const persist = useCallback((updater: GraphSettings | ((prev: GraphSettings) => GraphSettings)) => {
    setSettings((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      const result = trySaveSettings(next);
      setSaveDisabled(result.saveDisabled);
      setSaveNotice(
        result.saveDisabled ? "Settings cannot be saved — browser storage is unavailable or full." : null,
      );
      return next;
    });
  }, []);

  const setFilter = useCallback(
    (patch: Partial<GraphFilterState>) => {
      persist((prev) => ({ ...prev, filter: { ...prev.filter, ...patch } }));
    },
    [persist],
  );

  const setDisplay = useCallback(
    (patch: Partial<GraphDisplayState>) => {
      persist((prev) => ({ ...prev, display: { ...prev.display, ...patch } }));
    },
    [persist],
  );

  const setForce = useCallback(
    (patch: Partial<GraphForceState>) => {
      persist((prev) => ({ ...prev, force: { ...prev.force, ...patch } }));
    },
    [persist],
  );

  const setSectionsExpanded = useCallback(
    (patch: Partial<Record<GraphSectionKey, boolean>>) => {
      persist((prev) => ({
        ...prev,
        sectionsExpanded: { ...prev.sectionsExpanded, ...patch },
      }));
    },
    [persist],
  );

  const resetForces = useCallback(() => {
    persist((prev) => ({ ...prev, force: { ...DEFAULT_FORCE_STATE } }));
  }, [persist]);

  const resetAll = useCallback(() => {
    persist({
      ...DEFAULT_GRAPH_SETTINGS,
      filter: {
        ...DEFAULT_FILTER_STATE,
        enabledEdgeKinds: { ...defaultEnabledEdgeKinds },
      },
      sectionsExpanded: { ...DEFAULT_SECTIONS_EXPANDED },
    });
  }, [defaultEnabledEdgeKinds, persist]);

  useEffect(() => {
    const defaultKeys = Object.keys(defaultEnabledEdgeKinds);
    if (!defaultKeys.length) {
      return;
    }
    setSettings((prev) => {
      const merged = { ...defaultEnabledEdgeKinds, ...prev.filter.enabledEdgeKinds };
      const changed = defaultKeys.some((key) => !(key in prev.filter.enabledEdgeKinds));
      const wasEmpty = Object.keys(prev.filter.enabledEdgeKinds).length === 0;
      if (!changed && !wasEmpty) {
        return prev;
      }
      const next = {
        ...prev,
        filter: {
          ...prev.filter,
          enabledEdgeKinds: wasEmpty ? { ...defaultEnabledEdgeKinds } : merged,
        },
      };
      const result = trySaveSettings(next);
      setSaveDisabled(result.saveDisabled);
      setSaveNotice(
        result.saveDisabled ? "Settings cannot be saved — browser storage is unavailable or full." : null,
      );
      return next;
    });
  }, [defaultEnabledEdgeKinds]);

  return {
    settings,
    setFilter,
    setDisplay,
    setForce,
    setSectionsExpanded,
    resetForces,
    resetAll,
    saveDisabled,
    saveNotice,
  };
}
