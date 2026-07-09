// vitest setup: shim browser globals the components touch.
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});

if (typeof window !== "undefined") {
  // jsdom sometimes leaves localStorage unavailable. Define a
  // working shim via defineProperty to override the readonly getter.
  try {
    if (!window.localStorage || typeof window.localStorage.getItem !== "function") {
      const store: Record<string, string> = {};
      Object.defineProperty(window, "localStorage", {
        configurable: true,
        writable: true,
        value: {
          getItem: (k: string) => (k in store ? store[k] : null),
          setItem: (k: string, v: string) => {
            store[k] = String(v);
          },
          removeItem: (k: string) => {
            delete store[k];
          },
          clear: () => {
            for (const k of Object.keys(store)) delete store[k];
          },
          key: (i: number) => Object.keys(store)[i] ?? null,
          get length() {
            return Object.keys(store).length;
          },
        },
      });
    }
  } catch {
    // ignore — jsdom may have defined localStorage as non-configurable.
  }

  if (!window.matchMedia) {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  }
  // Mantine uses ResizeObserver; jsdom doesn't ship it.
  if (!window.ResizeObserver) {
    window.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    } as unknown as typeof ResizeObserver;
  }
}
