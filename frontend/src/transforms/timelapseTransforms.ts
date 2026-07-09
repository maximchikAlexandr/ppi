type TimelapseActionKind = "play" | "pause" | "prev" | "next" | "speed";

type CommitIdOnly = { readonly commit_hash: string } | { readonly commitId: string };

export type TimelapseInput = {
  readonly action: { kind: TimelapseActionKind; speed?: number };
  readonly commits: readonly CommitIdOnly[];
  readonly selectedCommit: string | null;
  readonly playing: boolean;
  readonly speed: number;
};

export type TimelapseOutput = {
  readonly playing: boolean;
  readonly speed: number;
  readonly selectedCommit: string | null;
};

function commitId(c: CommitIdOnly): string {
  return "commit_hash" in c ? c.commit_hash : c.commitId;
}

export function nextTimelapseState({
  action,
  commits,
  selectedCommit,
  playing,
  speed,
}: TimelapseInput): TimelapseOutput {
  if (commits.length < 2) {
    return { playing: false, speed, selectedCommit };
  }
  if (action.kind === "pause") {
    return { playing: false, speed, selectedCommit };
  }
  if (action.kind === "speed") {
    return { playing, speed: action.speed ?? speed, selectedCommit };
  }
  const index = commits.findIndex((row) => commitId(row) === selectedCommit);
  if (action.kind === "prev") {
    if (index > 0) {
      return { playing, speed, selectedCommit: commitId(commits[index - 1]!) };
    }
    return { playing, speed, selectedCommit };
  }
  if (action.kind === "next") {
    if (index < 0) {
      return { playing: false, speed, selectedCommit };
    }
    if (index >= commits.length - 1) {
      return { playing: false, speed, selectedCommit };
    }
    return { playing, speed, selectedCommit: commitId(commits[index + 1]!) };
  }
  if (action.kind === "play") {
    if (index < 0 || index >= commits.length - 1) {
      return { playing: true, speed, selectedCommit: commitId(commits[0]!) };
    }
    return { playing: true, speed, selectedCommit };
  }
  return { playing, speed, selectedCommit };
}
