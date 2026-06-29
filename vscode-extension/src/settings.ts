/**
 * Resolve effective PPI settings for a workspace folder.
 *
 * VS Code provides workspace-over-global precedence natively for `resource`
 * scope settings (FR-012); `machine-overridable` scope settings are resolved
 * globally here and may be overridden per-machine by the user.
 */

import * as vscode from "vscode";

import type { PpiSettings } from "./cliArgs";


const SECTION = "ppi";

/** Read effective settings for a workspace folder (or globally when null). */
export function readSettings(folder: vscode.WorkspaceFolder | null): PpiSettings {
  const cfg = vscode.workspace.getConfiguration(SECTION, folder ?? null);
  return {
    profile: (cfg.get<string>("profile") as "python" | "odoo") ?? "odoo",
    analysisDir: cfg.get<string>("analysisDir") ?? "",
    pythonExecutable: cfg.get<string>("pythonExecutable") ?? "",
    cliPath: cfg.get<string>("cliPath") ?? "",
  };
}

/** Guard the reserved `python` profile (FR-011): CLI supports only `odoo` at this stage.
 * If set to `python`, prompt to switch; persisting the switch keeps future runs silent.
 * Returns the effective profile, or `undefined` if the analyst cancelled. */
export async function resolveProfile(folder: vscode.WorkspaceFolder, settings: PpiSettings): Promise<"python" | "odoo" | undefined> {
  if (settings.profile !== "python") {
    return settings.profile;
  }
  const action = await vscode.window.showWarningMessage(
    "PPI: the `python` profile is reserved and not yet supported by the CLI. Use `odoo`.",
    "Switch to odoo",
    "Continue anyway",
  );
  if (action === "Continue anyway") {
    return "python";
  }
  if (action === "Switch to odoo") {
    const cfg = vscode.workspace.getConfiguration(SECTION, folder);
    await cfg.update("profile", "odoo", vscode.ConfigurationTarget.WorkspaceFolder);
    return "odoo";
  }
  return undefined;
}
