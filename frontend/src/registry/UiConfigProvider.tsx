import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { DefinitionRegistry } from "./DefinitionRegistry";
import type { UiConfig } from "./uiConfigTypes";

type Ctx = {
  config: UiConfig | null;
  registry: DefinitionRegistry | null;
  loading: boolean;
  error: string | null;
};

const UiConfigContext = createContext<Ctx>({
  config: null,
  registry: null,
  loading: true,
  error: null,
});

export function useUiConfig(): Ctx {
  return useContext(UiConfigContext);
}

export function UiConfigProvider({
  loader,
  children,
}: {
  loader: () => Promise<UiConfig>;
  children: ReactNode;
}) {
  const [config, setConfig] = useState<UiConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    loader()
      .then((cfg) => {
        if (alive) setConfig(cfg);
      })
      .catch((e: Error) => {
        if (alive) setError(e.message);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [loader]);

  const registry = useMemo(() => (config ? new DefinitionRegistry(config) : null), [config]);
  const value = useMemo(() => ({ config, registry, loading, error }), [
    config, registry, loading, error,
  ]);
  return <UiConfigContext.Provider value={value}>{children}</UiConfigContext.Provider>;
}
