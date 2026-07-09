import { map } from "remeda";

import type { CommitSummaryV1 } from "../api/publicApi";
import type { CommitRow } from "../api/client";

export type CommitOption = {
  readonly value: string;
  readonly label: string;
  readonly authoredAt: string | null | undefined;
  readonly commitOrder: number;
};

export function toCommitSelectOptions(commits: ReadonlyArray<CommitSummaryV1>): CommitOption[];
export function toCommitSelectOptions(commits: ReadonlyArray<CommitRow>): CommitOption[];
export function toCommitSelectOptions(commits: ReadonlyArray<CommitSummaryV1 | CommitRow>): CommitOption[] {
  return map(commits as ReadonlyArray<CommitSummaryV1 | CommitRow>, (row) => {
    const commitId = "commitId" in row ? row.commitId : row.commit_hash;
    const commitOrder = "commitOrder" in row ? row.commitOrder : row.commit_order;
    const authoredAt = "authoredAt" in row ? row.authoredAt : row.authored_at;
    const summary = "summary" in row ? row.summary : row.summary;
    return {
      value: commitId,
      label: `#${commitOrder} ${commitId.slice(0, 8)} ${summary ?? ""}`,
      authoredAt,
      commitOrder,
    };
  });
}

export function toCommitSelectOptionsShort(commits: ReadonlyArray<CommitSummaryV1>): { value: string; label: string }[];
export function toCommitSelectOptionsShort(commits: ReadonlyArray<CommitRow>): { value: string; label: string }[];
export function toCommitSelectOptionsShort(commits: ReadonlyArray<CommitSummaryV1 | CommitRow>): { value: string; label: string }[] {
  return map(commits as ReadonlyArray<CommitSummaryV1 | CommitRow>, (row) => {
    const commitId = "commitId" in row ? row.commitId : row.commit_hash;
    const commitOrder = "commitOrder" in row ? row.commitOrder : row.commit_order;
    return {
      value: commitId,
      label: `#${commitOrder} ${commitId.slice(0, 8)}`,
    };
  });
}