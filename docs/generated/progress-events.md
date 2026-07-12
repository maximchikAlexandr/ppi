<!-- Generated file. Do not edit manually. Source: ppi.runtime.progress::ProgressEvent. Generator: progress. -->

# Progress Events Reference

Automatically generated from `src/ppi/runtime/progress.py`.


## run_started

| Field | Value |
|-------|-------|
| Tag | `run_started` |

| run_id | `string` |

| branch | `string` |

| mode | `'incremental' | 'rebuild'` |

| commits_total | `number` |



## commit_progress

| Field | Value |
|-------|-------|
| Tag | `commit_progress` |

| processed | `number` |

| commits_total | `number` |

| short_hash | `string` |



## run_completed

| Field | Value |
|-------|-------|
| Tag | `run_completed` |

| run_id | `string` |

| commits_succeeded | `number` |

| commits_failed | `number` |

| duration_ms | `number` |



## run_failed

| Field | Value |
|-------|-------|
| Tag | `run_failed` |

| run_id | `string` |

| exit_reason | `string` |

| message | `string` |

| stderr_tail | `string` |


