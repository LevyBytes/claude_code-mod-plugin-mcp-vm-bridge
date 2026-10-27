# Sidebar compatibility qualification

Automatic new/resume uses a version-specific VS Code command contract. The adapter intentionally rejects unknown
extension builds. Matching a version label alone is insufficient.

The current allowlist is in `sidebar_companion/routing.js`. The pilot's accepted 2.1.310 source hash belongs to its
existing environment, which included an earlier history-picker patch. It is not evidence that every stock 2.1.310
installation matches. This repository does not distribute or apply that patch.

To qualify another build:

1. Run `python -B inspect_sidebar.py` to record the installed version, SHA-256 and current editor-tab state.
2. Inspect that extension's command registration and handler for `claude-vscode.editor.open`.
   Verify the positional arguments, the `programmatic: honor-preferred-location` option, sidebar focus command
   and `preferredLocation` behavior. A string match alone does not establish the handler's semantics.
3. In a disposable contained profile, test a new conversation and a completed prior conversation. Verify the exact
   session ID, right sidebar placement, no editor tab and no submitted prompt. Do not use interrupted history for the
   no-continuation check: provider settings can resume interrupted work on their own.
4. Update the adapter's exact version/hash only after those checks. Keep tests rejecting other hashes, unexpected
   arguments and ambiguous editor tabs. If the handler contract changed, adapt the handler and its regression tests.
5. Rebuild, run host conformance and the native validator, install the rebuilt VSIX, and repeat sidebar inspection.
   Keep the evidence with that release's compatibility notes.

Do not offer a flag that blindly trusts arbitrary hashes. Until qualification passes, manually open a Claude sidebar
conversation; the mod's message/status/context controls are separate from automated sidebar new/resume.
