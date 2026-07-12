// Generated file. Do not edit manually.
// Source: ppi.runtime.progress::ProgressEvent
// Generator: progress

export interface RunStarted {
    type: "run_started";
    run_id: string;
    branch: string;
    mode: 'incremental' | 'rebuild';
    commits_total: number;
}}

export interface CommitProgress {
    type: "commit_progress";
    processed: number;
    commits_total: number;
    short_hash: string;
}}

export interface RunCompleted {
    type: "run_completed";
    run_id: string;
    commits_succeeded: number;
    commits_failed: number;
    duration_ms: number;
}}

export interface RunFailed {
    type: "run_failed";
    run_id: string;
    exit_reason: string;
    message: string;
    stderr_tail?: string;
}}

export type ProgressEvent =
    RunStarted |
    CommitProgress |
    RunCompleted |
    RunFailed;
