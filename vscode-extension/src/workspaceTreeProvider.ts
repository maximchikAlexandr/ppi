/** Empty tree so VS Code shows the contributed viewsWelcome (post-install entrypoint). */
import * as vscode from "vscode";

export function registerWorkspaceView(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.window.createTreeView("ppi.workspace", {
      treeDataProvider: { getTreeItem: (e) => e, getChildren: () => [] },
    }),
  );
}