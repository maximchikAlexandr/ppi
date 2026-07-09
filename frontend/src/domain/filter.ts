export type FilterDefinition = {
  id: string;
  label: string;
  kind: "select" | "multi" | "boolean" | "number" | "text";
  options?: FilterOption[];
};

export type FilterOption = {
  id: string;
  label: string;
};

export type FilterValue = string | string[] | number | boolean | null;
