<!-- Generated file. Do not edit manually. Source: contracts/errors.yaml. Generator: errors. -->

# Error Codes Reference

Automatically generated from `contracts/errors.yaml`.


## INVALID_REQUEST

| Field | Value |
|-------|-------|
| Code | `INVALID_REQUEST` |
| Category | `client` |
| Default Message | Invalid request. |
| Retryable | False |
| Stability | public |
| Description | Request payload or parameters are invalid. |
| HTTP Status | 400 |







## INTERNAL_ERROR

| Field | Value |
|-------|-------|
| Code | `INTERNAL_ERROR` |
| Category | `server` |
| Default Message | An internal error occurred. |
| Retryable | True |
| Stability | internal |
| Description | Unexpected server error. |
| HTTP Status | 500 |







## NOT_FOUND

| Field | Value |
|-------|-------|
| Code | `NOT_FOUND` |
| Category | `client` |
| Default Message | Resource not found. |
| Retryable | False |
| Stability | public |
| Description | Requested resource does not exist. |
| HTTP Status | 404 |







## VALIDATION_ERROR

| Field | Value |
|-------|-------|
| Code | `VALIDATION_ERROR` |
| Category | `client` |
| Default Message | Validation error. |
| Retryable | False |
| Stability | public |
| Description | Input validation failed. |
| HTTP Status | 422 |







## WORKSPACE_ERROR

| Field | Value |
|-------|-------|
| Code | `WORKSPACE_ERROR` |
| Category | `workspace` |
| Default Message | Workspace error. |
| Retryable | True |
| Stability | experimental |
| Description | Workspace-related error. |








## RATE_LIMITED

| Field | Value |
|-------|-------|
| Code | `RATE_LIMITED` |
| Category | `transport` |
| Default Message | Rate limited. |
| Retryable | True |
| Stability | public |
| Description | Request was rate limited. |
| HTTP Status | 429 |







## DEPRECATED_FEATURE

| Field | Value |
|-------|-------|
| Code | `DEPRECATED_FEATURE` |
| Category | `runtime` |
| Default Message | This feature is deprecated. |
| Retryable | False |
| Stability | deprecated |
| Description | Deprecated error. |








## STORE_NOT_READY

| Field | Value |
|-------|-------|
| Code | `STORE_NOT_READY` |
| Category | `server` |
| Default Message | Storage is not ready. |
| Retryable | True |
| Stability | internal |
| Description | Database or storage backend is unavailable. |
| HTTP Status | 503 |






