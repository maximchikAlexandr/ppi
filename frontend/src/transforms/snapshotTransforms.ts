type CommitLike =
  | { commit_hash: string; commit_order?: number; summary?: string | null }
  | { commitId: string; commitOrder?: number; summary?: string | null };

function commitId(c: CommitLike): string {
  return "commit_hash" in c ? c.commit_hash : c.commitId;
}

function commitOrder(c: CommitLike): number {
  if ("commit_order" in c) {
    return c.commit_order ?? 0;
  }
  return (c as { commitOrder?: number }).commitOrder ?? 0;
}

function commitSummary(c: CommitLike): string | null {
  return c.summary ?? null;
}

type NodeLike = { module_name: string } | { entity: { id: string } };

function nodeName(n: NodeLike): string {
  return "module_name" in n ? n.module_name : n.entity.id;
}

export function commitPositionLabel(commits: ReadonlyArray<CommitLike>, commitHash: string | null): string {
  if (!commitHash) {
    return "—";
  }
  const index = commits.findIndex((row) => commitId(row) === commitHash);
  if (index < 0) {
    return "—";
  }
  const row = commits[index]!;
  return `${index + 1} / ${commits.length} · #${commitOrder(row)} ${commitId(row).slice(0, 8)} ${commitSummary(row) ?? ""}`;
}

export function resolveProjectStorageKey(
  projectId: string | null | undefined,
  repoPath: string | null | undefined,
  originPathname: string,
): string | null {
  if (projectId) {
    return projectId;
  }
  if (repoPath) {
    return repoPath;
  }
  if (originPathname) {
    return originPathname;
  }
  return null;
}

export function resolveGraphSelection(
  nodes: ReadonlyArray<NodeLike>,
  focusModule: string | null,
): { selectedModule: string | null; clearFocus: boolean; notice: string | null } {
  if (focusModule && nodes.some((node) => nodeName(node) === focusModule)) {
    return { selectedModule: focusModule, clearFocus: false, notice: null };
  }
  if (focusModule && nodes.length > 0) {
    return {
      selectedModule: null,
      clearFocus: true,
      notice: `Focused module "${focusModule}" is not present at this commit. Focus cleared.`,
    };
  }
  return { selectedModule: null, clearFocus: false, notice: null };
}
