# Development and operation

## Source and local workspace

Maintain `claude_session/`, `bridge_runtime/`, `mod/src/`, `mod/tests/`, `sidebar_companion/`, `tools/` and `tests/`.
Source files are limited to **100 physical lines and 120 characters per line**, including comments and blank lines.
Text uses UTF-8 and LF. The build joins the mod modules into one entry file; generated output is hash-checked.

The repository holds source, tests, product documentation and build tooling. Generated outputs stay in `build/` and `dist/`.
AI instructions, session notes, machine configuration, local dependencies, logs and receipts live outside the repo.

## Build and verify

Use Python 3.12+, Node.js and Pyright. Ruff is pinned in [requirements-dev.txt](../requirements-dev.txt).
For a Windows development setup with `DEVROOT` configured, run from the source repository, example:

```powershell
$work = Join-Path $env:DEVROOT 'PROJECTS/Kaizen_claude_code_mod_orchestration_vm_bridge'
New-Item -ItemType Directory -Force "$work/runtime/tmp" | Out-Null
$env:TEMP = $env:TMP = "$work/runtime/tmp"
python -B -m pip install --no-cache-dir --target "$work/.tools/python" -r requirements-dev.txt
python -B build.py
python -B conformance.py
```

Use your chosen Python interpreter for those commands. No PATH changes are required.
Conformance checks source limits, encoding, Python/JSON/TOML syntax, Ruff, Pyright, Python tests,
Node tests, compiled mod syntax, release contents and build freshness. Missing tools fail the check.
`--source-only` is explicitly partial. Check receipts are written to the external workspace.

Outputs are `build/plugin/`, `build/host/`, `build/claude-sidebar-bridge.vsix`, `build/manifest.json`,
and `dist/claude-vm-bridge-0.3.0.zip`. The plugin, host build, VSIX and ZIP include Apache LICENSE and NOTICE files.

## Connect

For a new installation, follow [first setup](setup.md), including real mapping proofs and initial plugin loading.

The external workspace's `runtime/instance.json` binds the bridge to an explicitly selected Podman instance
and its approved mounts. An existing configured environment is required; this is not an all-in-one VM installer.

```powershell
python -B bridge.py capabilities
python -B bridge.py sessions
python -B bridge.py mcp
```

The CLI and stdio MCP use the same transport. MCP exposes ten `claude_*` tools: capabilities, sessions, status,
events, send, interrupt, request, configure, context and open. Refresh session bindings before mutations.
`register_mcp.py` creates or updates the `kaizen_claude_vm` Codex registration for this checkout and external workspace.
A running client may need to reload or rediscover the server. Registration does not prove discovery.

## Update an existing deployment

After editing source, rebuild and run conformance. `python -B check_native.py` runs Claude's offline validator
and mod tests inside isolated guest configuration; it requires the configured VM and submits no model prompts.

`update.py` previews destinations. `update.py --apply` rechecks conformance/native tests, requires idle sessions,
and proves the host-to-guest mappings before publishing frozen bytes to the configured source grants.
It backs up overwritten/obsolete files and removes only obsolete managed output. Unrecognized files stop the update.
Mounts and provider data are unchanged.
Older instance files need one verified `configure_instance.py --apply` binding before an update.
`refresh.py` reloads the owned relay and contained editor. Refresh invalidates session bindings and model overrides.
The sidebar VSIX is installed separately into the contained profile when its code changes.

An interrupted deployment is not a successful update. Reconcile the recorded backup manifest before activation;
the publisher is not crash-atomic across multiple files. No uncertain model request is automatically resent.
See [delivery and recovery](delivery.md) and [sidebar qualification](sidebar_qualification.md) for exact guarantees.
