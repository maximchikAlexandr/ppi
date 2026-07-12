# Contract: Webview postMessage Protocol

## Source of truth

```text
contracts/webview-protocol.schema.json
```

This schema describes only messages crossing the webview-extension `postMessage` boundary.

## Generated files

```text
frontend/src/generated/webviewProtocol.ts
frontend/src/generated/webviewProtocolValidators.ts
vscode-extension/src/generated/webviewProtocol.ts
vscode-extension/src/generated/webviewProtocolValidators.ts
docs/generated/webview-protocol.md
```

## Facades

```text
frontend/src/contracts/webviewProtocol.ts
vscode-extension/src/contracts/webviewProtocol.ts
```

## Runtime validation

All unknown webview messages must be validated with Ajv validators generated from the JSON Schema.

Do not use React component types, frontend-only TypeScript types, extension implementation types, Zod schemas, or manual type guards as source of truth.
