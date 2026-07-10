import { map } from "remeda";

import type { CommitSummaryV1 } from "../api/publicApi";

export type CommitOption = {
  readonly value: string;
  readonly label: string;
  readonly authoredAt: string | null | undefined;
  readonly commitOrder: number;
};

type CommitLike =
  | CommitSummaryV1
  | { commitId: string; commitOrder: number; authoredAt?: string | null; summary?: string | null }
  | { commit_hash: string; commit_order: number; authored_at?: string | null; summary?: string | null };

function toV1(row: CommitLike): CommitSummaryV1 {
  if ("commitId" in row) {
    return {
      commitId: row.commitId,
      commitOrder: row.commitOrder,
      authoredAt: row.authoredAt ?? null,
      summary: row.summary ?? null,
    };
  }
  return {
    commitId: row.commit_hash,
    commitOrder: row.commit_order,
    authoredAt: row.authored_at ?? null,
    summary: row.summary ?? null,
  };
}

export function toCommitSelectOptions(commits: ReadonlyArray<CommitLike>): CommitOption[] {
  return map(commits, (row) => {
    const v = toV1(row);
    return {
      value: v.commitId,
      label: `#${v.commitOrder} ${v.commitId.slice(0, 8)} ${v.summary ?? ""}`,
      authoredAt: v.authoredAt,
      commitOrder: v.commitOrder,
    };
  });
}

export function toCommitSelectOptionsShort(commits: ReadonlyArray<CommitLike>): { value: string; label: string }[] {
  return map(commits, (row) => {
    const v = toV1(row);
    return {
      value: v.commitId,
      label: `#${v.commitOrder} ${v.commitId.slice(0, 8)}`,
    };
  });
}
