# Generated file. Do not edit manually.
# Source: ppi.runtime.progress::ProgressEvent
# Generator: progress

from __future__ import annotations

PROGRESS_EVENT_SCHEMA: dict = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ProgressEvent",
  "oneOf": [
    {
      "type": "object",
      "properties": {
        "type": {
          "const": "run_started"
        },
        "run_id": {
          "type": "string"
        },
        "branch": {
          "type": "string"
        },
        "mode": {
          "enum": [
            "incremental",
            "rebuild"
          ]
        },
        "commits_total": {
          "type": "integer"
        }
      },
      "required": [
        "type",
        "run_id",
        "branch",
        "mode",
        "commits_total"
      ]
    },
    {
      "type": "object",
      "properties": {
        "type": {
          "const": "commit_progress"
        },
        "processed": {
          "type": "integer"
        },
        "commits_total": {
          "type": "integer"
        },
        "short_hash": {
          "type": "string"
        }
      },
      "required": [
        "type",
        "processed",
        "commits_total",
        "short_hash"
      ]
    },
    {
      "type": "object",
      "properties": {
        "type": {
          "const": "run_completed"
        },
        "run_id": {
          "type": "string"
        },
        "commits_succeeded": {
          "type": "integer"
        },
        "commits_failed": {
          "type": "integer"
        },
        "duration_ms": {
          "type": "integer"
        }
      },
      "required": [
        "type",
        "run_id",
        "commits_succeeded",
        "commits_failed",
        "duration_ms"
      ]
    },
    {
      "type": "object",
      "properties": {
        "type": {
          "const": "run_failed"
        },
        "run_id": {
          "type": "string"
        },
        "exit_reason": {
          "type": "string"
        },
        "message": {
          "type": "string"
        },
        "stderr_tail": {
          "type": "string"
        }
      },
      "required": [
        "type",
        "run_id",
        "exit_reason",
        "message"
      ]
    }
  ]
}
