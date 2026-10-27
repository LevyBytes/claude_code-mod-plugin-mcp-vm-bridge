# First setup

The supported layout is one existing Linux desktop container with Python 3.12+, full VS Code, and Claude Code.
The guest user is UID/GID 1000:1000 with home `/home/kaizen`; VS Code opens `/workspace`.
This package connects that environment. It does not install Podman, a Linux image, a desktop or provider credentials.

Keep the host controller workspace outside guest-writable mappings. On Windows the default is
`$DEVROOT/PROJECTS/Kaizen_claude_code_mod_orchestration_vm_bridge`.
Without DEVROOT, it is `PROJECTS/Kaizen_claude_code_mod_orchestration_vm_bridge` beside the checkout.
An absolute `CLAUDE_VM_BRIDGE_WORKSPACE` overrides it. Registration records that override for the MCP subprocess.

## 1. Build and prepare dedicated source grants

Run the dependencies/build/check commands in [development](development.md). Then, from the source checkout:

```powershell
$work = Join-Path $env:DEVROOT 'PROJECTS/Kaizen_claude_code_mod_orchestration_vm_bridge'
$tools = Join-Path $work 'deployment/session-tools'
$mod = Join-Path $work 'deployment/claude-session-mod'
python -B prepare_deployment.py --guest-tools "$tools" --mod "$mod"
```

This populates new, empty directories from the checked build. It refuses nonempty directories.
These two directories are dedicated generated deployment outputs, never a project root or a provider-state directory.
The updater records which files it owns, backs up overwritten files and removes obsolete managed output.
Unexpected untracked files stop the update; they are never silently deleted.

Mount them read-only in the selected container:

| Host directory | Container destination |
| --- | --- |
| `$tools` | `/opt/kaizen/session-tools` |
| `$mod` | `/opt/kaizen/claude-session-mod` |

For a Windows Podman machine, the mount source is the Linux VM path that exposes that host directory, not necessarily
the Windows path. For example, an existing VM bind may expose it under `/pilot-maps/session-tools`.
Arrange these two mappings through your existing VM/container creation workflow. Do not expose the whole controller
workspace or the Podman socket. Provider credentials and project mappings remain the owner's separate selections.

## 2. Verify the real mapping and create the instance file

Use the actual running container name and Podman connection. For example:

```powershell
$podman = (Get-Command podman -ErrorAction Stop).Source
$container = 'your-desktop-container'
python -B configure_instance.py --podman "$podman" --container "$container" --guest-tools "$tools" --mod "$mod"
python -B configure_instance.py --podman "$podman" --container "$container" --guest-tools "$tools" --mod "$mod" --apply
```

Add `--connection your-connection` to both commands when needed. Portable Podman deployments can pass
`--environment-file /absolute/path/to/podman-environment.json`, an external JSON object of environment string values.

The first command previews the observed container/mount identity. `--apply` writes a random proof file into each
selected host directory, reads it through the guest mapping, removes it, then records the verified relationship in
the external `runtime/instance.json`. A wrong alias or folder fails. Existing instance configuration is backed up.
An update repeats the proof before writing. Neither command creates a VM or changes its mounts.

The [configuration example](instance.example.json) documents the fields. Generate the real file with this command;
the example's synthetic IDs and paths are not a usable instance binding.

## 3. Start the guest relay and load the mod

In a guest terminal, as the desktop user:

```sh
python3 -B /opt/kaizen/session-tools/relay.py
```

Keep this process running, or add the same command to your existing desktop startup workflow before VS Code starts.
The relay binds guest loopback only. Its private token and request journal stay in
`/home/kaizen/.local/state/kaizen-session/`. The container needs a writable native Linux home for these files.

Merge this environment setting into the guest-specific Claude settings, preserving other settings:

```json
{"env": {"CLAUDE_CODE_PLUGIN_DIRS": "/opt/kaizen/claude-session-mod"}}
```

Use the Linux replacement settings file when Windows settings are shared. Do not overwrite the host's settings.
Reload the contained VS Code window after the relay and plugin are ready. Host and guest must use the same built
protocol version (currently 3); older mods cannot be controlled by the updated relay.

For the tested profile, install the built companion VSIX into
`/home/kaizen/editor-state/extensions` and launch VS Code with
`--user-data-dir=/home/kaizen/editor-state/user-data --extensions-dir=/home/kaizen/editor-state/extensions /workspace`.
Transfer only `build/claude-sidebar-bridge.vsix` using your existing project mapping or `podman cp`.
Inside the guest:

```sh
code --user-data-dir=/home/kaizen/editor-state/user-data --extensions-dir=/home/kaizen/editor-state/extensions --install-extension /path/to/claude-sidebar-bridge.vsix
```

For other profile locations, basic mod controls may work, but the supplied refresh/native-check scripts assume the
tested profile above. Do not run refresh against a different profile.

## 4. Check controls and register the MCP server

From the host checkout:

```powershell
python -B check_native.py
python -B inspect_sidebar.py
python -B bridge.py sessions
python -B register_mcp.py
```

Native checking runs Claude's offline validator/test kit without model generation. Sidebar inspection reports the
installed extension version/hash and qualification result. See [qualification](sidebar_qualification.md) for an unknown
build; do not bypass the gate. A manually opened sidebar session can still expose mod controls while automated
new/resume remains unavailable for an unqualified companion build.

Registration creates or updates only the `kaizen_claude_vm` MCP entry and preserves unrelated parsed configuration.
It uses the selected Python interpreter and external workspace. Reload Codex's MCP connection afterward.
The server automatically recognizes supported caller ancestry; running control commands from an ordinary human shell
does not impersonate Codex. Read-only status remains available. Local agent applications integrate through
`RuntimeConnection`; the inference/tool loop is supplied by that application.

Do not report installation as qualified until your actual guest validator, sidebar check and session observation pass.
No model prompt is needed for those checks. Live orchestration and interruption require their own test.
