# Contract: Error Codes

## Source

```text
contracts/errors.yaml
```

## Required manifest shape

```yaml
version: 1
owner: backend
errors:
  - code: INVALID_REQUEST
    category: client
    defaultMessage: Invalid request.
    retryable: false
    stability: public
    description: Request payload or parameters are invalid.
    httpStatus: 400
```

## Required fields per entry

```text
code
category
defaultMessage
retryable
stability
description
```

## Optional fields

```text
httpStatus
rpcCode
cliExitCategory
webviewActionMapping
replacement
removalNote
```

## Generated files

```text
src/ppi/generated/errors.py
frontend/src/generated/errorCodes.ts
vscode-extension/src/generated/errorCodes.ts
docs/generated/errors.md
```

## Handwritten facades

```text
src/ppi/contracts/errors.py
frontend/src/contracts/errorCodes.ts
vscode-extension/src/contracts/errorCodes.ts
```

## Validation rules

- `code` must be uppercase snake case.
- Duplicate `code` values are invalid.
- `category` must be one of `client`, `server`, `runtime`, `workspace`, `contract`, `transport`, `extension`, `unknown`.
- `stability` must be one of `internal`, `experimental`, `public`, `deprecated`.
- `description` is required for all entries.
- Deprecated entries require `replacement` or `removalNote`.
- `httpStatus` is optional.
