export type CapabilityDefinition = {
  id: string;
  label: string;
  enabled: boolean;
  reason?: string | null;
};

export type PageKind =
  | "snapshot"
  | "dashboard"
  | "tables"
  | "diagnostics"
  | "custom";

export type PageDefinition = {
  id: string;
  label: string;
  kind: PageKind;
  requiredCapabilities: string[];
  defaultVisible: boolean;
};
