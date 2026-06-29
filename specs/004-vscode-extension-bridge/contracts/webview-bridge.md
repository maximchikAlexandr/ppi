# Contract: Webview ↔ extension message bridge

**Owner**: `webviewPanel.ts` (extension) + `dataSource.ts`/`webview-main.tsx` (frontend).
**Spec ref**: FR-008, FR-018, FR-010, SC-003.

Transport: `vscode.postMessage` (Webview → extension) and `panel.webview.postMessage` (extension → Webview). All messages are JSON with a `kind` discriminator.

## Request (Webview → extension)

```json
{"kind":"request","id":42,"method":"graph","params":{"commit":null,"include_zero_score":false}}
```
- `method`/`params` match the `ppi rpc` contract (`cli-query-surface.md`).
- The extension forwards this as an `RpcRequest` to the `ppi rpc` servant and posts the matching response back.

## Response (extension → Webview)

```json
{"kind":"response","status":"ok","id":42,"result":{...}}
```
or
```json
{"kind":"response","status":"error","id":42,"error":{"code":"STORE_NOT_FOUND","message":"..."}}
```
- Discriminated union on `status`: exactly one of `result`/`error`, never both, never neither.
- Exactly one response per `request.id` (correlation). `WebviewDataSource` resolves/rejects a per-id promise.
- `method` is allowlisted to read-only `ppi rpc` methods; any other method returns `status:"error"` with code `METHOD_NOT_ALLOWED`.

## Command (Webview → extension)

```json
{"kind":"command","command":"ppi.analyze"}
```
Closed enum: `ppi.analyze`, `ppi.openSettings`, `ppi.cancelAnalysis`. Used by the dashboard empty state "Run analysis" button (FR-010) and the profile/interpreter error "Open Settings" action.

## Event (extension → Webview)

```json
{"kind":"event","event":"runStarted","run_id":"...","commits_total":412}
{"kind":"event","event":"progress","processed":7,"commits_total":412,"short_hash":"a1b2c3d4"}
{"kind":"event","event":"runCompleted","commits_succeeded":410,"commits_failed":2}
{"kind":"event","event":"runFailed","message":"...","stderr_tail":"..."}
{"kind":"event","event":"runCancelled"}
```
The dashboard may show a lightweight run banner from these events; primary progress UI is the VS Code status bar + notifications (FR-002/FR-003).

## Data source abstraction (frontend)

```ts
interface DataSource {
  get<T>(method: string, params?: Record<string, unknown>): Promise<T>;
  post<T>(method: string, body: unknown): Promise<T>;
}
```
- `HttpDataSource`: `get` → `fetch("/api/<method>?<params>")`; `post` → `fetch("/api/<method>", {method:"POST", body})`. (Browser, unchanged behavior.)
- `WebviewDataSource`: `get`/`post` → post a `request` message, await `response` by `id`.
- `client.ts` `fetch*` helpers delegate to an injected `DataSource` (set at bootstrap). `method` here corresponds to the `/api` path tail (e.g. `graph`, `snapshot/modules`, `edge-points/batch`).

## CSP

The Webview HTML sets a strict Content Security Policy using the dynamic `webview.cspSource` (NOT the deprecated literal `vscode-resource:` scheme) and a per-load nonce. Scripts load from `webview.asWebviewUri(...)` pointing at the built `dist-webview` bundle, each tag carrying the nonce; no inline scripts without a nonce; no remote hosts. See `contracts/extension-manifest.md`.
