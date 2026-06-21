import { hierarchy, treemap, treemapSquarify } from "d3-hierarchy";
import { useEffect, useMemo, useRef, useState } from "react";

import type { FileSnapshot } from "../api/client";
import { LINE_CATEGORIES, type LineCategoryKey } from "../registry/odooProfile";
import { compactLines, formatCodeLines, formatStatsLine } from "../utils/metricFormat";

type Props = {
  files: FileSnapshot[];
  lineCategories: Set<LineCategoryKey>;
  selectedPath: string | null;
  onSelect: (file: FileSnapshot | null) => void;
  onHover?: (file: FileSnapshot | null) => void;
};

type TreemapRoot = {
  children: FileSnapshot[];
};

type TreemapLeaf = {
  file: FileSnapshot;
  x0: number;
  x1: number;
  y0: number;
  y1: number;
};

const FOLDER_COLORS = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc949", "#af7aa1", "#ff9da7"];
const MIN_TEXT_WIDTH = 60;
const MIN_TEXT_HEIGHT = 28;

function categoryLabel(category: string): string {
  return LINE_CATEGORIES.find(({ key }) => key === category)?.label ?? category;
}

function fileTooltip(file: FileSnapshot): string {
  const parts = [
    `${file.module_name}/${file.relative_path}`,
    `lines=${formatCodeLines(file.lines)}`,
    categoryLabel(file.category),
    `CC ${formatStatsLine(file.cyclomatic)}`,
    `cognitive ${formatStatsLine(file.cognitive)}`,
    `Jones ${formatStatsLine(file.jones)}`,
  ];
  if (file.parse_error) {
    parts.push(`parse_error=${file.parse_error}`);
  }
  return parts.join(" | ");
}

function folderColor(topFolder: string): string {
  let hash = 0;
  for (let index = 0; index < topFolder.length; index += 1) {
    hash = topFolder.charCodeAt(index) + ((hash << 5) - hash);
  }
  return FOLDER_COLORS[Math.abs(hash) % FOLDER_COLORS.length];
}

function isFileSnapshot(value: TreemapRoot | FileSnapshot): value is FileSnapshot {
  return "relative_path" in value;
}

function truncateText(text: string, maxChars: number): string | null {
  if (maxChars < 3) {
    return null;
  }
  if (text.length <= maxChars) {
    return text;
  }
  return `${text.slice(0, Math.max(1, maxChars - 1))}…`;
}

export function FileTreemap({ files, lineCategories, selectedPath, onSelect, onHover }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 860, height: 560 });

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }
    const observer = new ResizeObserver(([entry]) => {
      const width = Math.max(320, Math.floor(entry.contentRect.width));
      setSize({ width, height: 560 });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const filtered = useMemo(
    () =>
      files.filter((file) => {
        if (!lineCategories.size) {
          return false;
        }
        return lineCategories.has(file.category as LineCategoryKey);
      }),
    [files, lineCategories],
  );

  const layout = useMemo(() => {
    if (!filtered.length) {
      return [] as TreemapLeaf[];
    }
    const root = hierarchy<TreemapRoot | FileSnapshot>({ children: filtered })
      .sum((node) => (isFileSnapshot(node) ? node.lines : 0))
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
    return treemap<TreemapRoot | FileSnapshot>()
      .tile(treemapSquarify)
      .size([size.width, size.height])
      .padding(2)(root)
      .leaves()
      .flatMap((leaf) => {
        if (!isFileSnapshot(leaf.data)) {
          return [];
        }
        return [{
          file: leaf.data,
          x0: leaf.x0,
          x1: leaf.x1,
          y0: leaf.y0,
          y1: leaf.y1,
        }];
      });
  }, [filtered, size.height, size.width]);

  const legend = [...new Set(filtered.map((file) => file.top_folder))];

  if (!filtered.length) {
    return (
      <div ref={containerRef} style={{ padding: 24, color: "#868e96" }}>
        No files for the selected line categories.
      </div>
    );
  }

  return (
    <div ref={containerRef}>
      <div style={{ display: "flex", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
        {legend.map((folder) => (
          <span key={folder} style={{ fontSize: 12 }}>
            <span
              style={{
                display: "inline-block",
                width: 12,
                height: 12,
                background: folderColor(folder),
                marginRight: 4,
              }}
            />
            {folder}
          </span>
        ))}
      </div>
      <svg
        width="100%"
        height={size.height}
        viewBox={`0 0 ${size.width} ${size.height}`}
        style={{ border: "1px solid var(--mantine-color-gray-3)", background: "#fbfcfd", display: "block" }}
      >
        {layout.map((leaf) => {
          const file = leaf.file;
          const pathKey = `${file.module_name}/${file.relative_path}`;
          const selected = selectedPath === pathKey;
          const innerW = leaf.x1 - leaf.x0;
          const innerH = leaf.y1 - leaf.y0;
          const centerX = leaf.x0 + innerW / 2;
          const centerY = leaf.y0 + innerH / 2;
          const maxChars = Math.floor((innerW - 6) / 6.8);
          const basename = file.relative_path.split("/").pop() ?? file.relative_path;
          const displayName = truncateText(basename, maxChars);
          const displayLines = truncateText(compactLines(file.lines), maxChars);
          return (
            <g
              key={pathKey}
              transform={`translate(${leaf.x0}, ${leaf.y0})`}
              onClick={() => onSelect(file)}
              onMouseEnter={() => onHover?.(file)}
              onMouseLeave={() => onHover?.(null)}
              style={{ cursor: "pointer" }}
            >
              <title>{fileTooltip(file)}</title>
              <rect
                width={innerW}
                height={innerH}
                fill={folderColor(file.top_folder)}
                stroke={selected ? "#228be6" : "#fff"}
                strokeWidth={selected ? 2 : 1}
              />
              {innerW >= MIN_TEXT_WIDTH && innerH >= MIN_TEXT_HEIGHT ? (
                <>
                  {displayName ? (
                    <text
                      x={centerX - leaf.x0}
                      y={displayLines ? centerY - leaf.y0 - 2 : centerY - leaf.y0 + 4}
                      textAnchor="middle"
                      fontSize={12}
                      fontWeight={600}
                      fill="#ffffff"
                      pointerEvents="none"
                    >
                      {displayName}
                    </text>
                  ) : null}
                  {displayLines ? (
                    <text
                      x={centerX - leaf.x0}
                      y={displayName ? centerY - leaf.y0 + 14 : centerY - leaf.y0 + 4}
                      textAnchor="middle"
                      fontSize={12}
                      fill="#ffffff"
                      pointerEvents="none"
                    >
                      {displayLines}
                    </text>
                  ) : null}
                </>
              ) : null}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
