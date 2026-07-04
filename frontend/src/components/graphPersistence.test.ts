import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { loadSettingsFromStorage, trySaveSettings } from "./graphPersistence";
import { DEFAULT_GRAPH_SETTINGS, DEFAULT_SECTIONS_EXPANDED, SETTINGS_STORAGE_KEY } from "./graphSettingsTypes";

describe("graphPersistence", () => {
  beforeEach(() => {
    const values = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => {
        values.set(key, value);
      },
      removeItem: (key: string) => {
        values.delete(key);
      },
      clear: () => {
        values.clear();
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("preserves all graph settings accordion sections", () => {
    expect(Object.keys(DEFAULT_SECTIONS_EXPANDED)).toEqual([
      "lineCategories",
      "brightness",
      "filters",
      "display",
      "forces",
      "focus",
    ]);

    const settings = {
      ...DEFAULT_GRAPH_SETTINGS,
      sectionsExpanded: {
        ...DEFAULT_SECTIONS_EXPANDED,
        lineCategories: true,
        brightness: true,
        filters: false,
      },
    };

    expect(trySaveSettings(settings).ok).toBe(true);

    const loaded = loadSettingsFromStorage({ extension_or_method: true }, ["visible_lines"], ["score"]);
    expect(loaded.settings.sectionsExpanded.lineCategories).toBe(true);
    expect(loaded.settings.sectionsExpanded.brightness).toBe(true);
    expect(loaded.settings.sectionsExpanded.filters).toBe(false);
  });

  it("fills newly introduced section keys when loading old settings", () => {
    localStorage.setItem(
      SETTINGS_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        filter: DEFAULT_GRAPH_SETTINGS.filter,
        display: DEFAULT_GRAPH_SETTINGS.display,
        force: DEFAULT_GRAPH_SETTINGS.force,
        sectionsExpanded: {
          filters: false,
          display: true,
          forces: true,
          focus: true,
        },
      }),
    );

    const loaded = loadSettingsFromStorage({ extension_or_method: true }, ["visible_lines"], ["score"]);
    expect(loaded.settings.sectionsExpanded.lineCategories).toBe(false);
    expect(loaded.settings.sectionsExpanded.brightness).toBe(false);
    expect(loaded.settings.sectionsExpanded.filters).toBe(false);
  });
});
