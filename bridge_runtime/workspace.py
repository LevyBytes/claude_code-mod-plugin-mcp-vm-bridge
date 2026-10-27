"""Resolve external local state without putting machine/session data in the source checkout."""
import os
from pathlib import Path

WORKSPACE_NAME = 'Kaizen_claude_code_mod_orchestration_vm_bridge'


def resolve_workspace(source_root: Path, environment=None) -> Path:
    env = os.environ if environment is None else environment
    override = env.get('CLAUDE_VM_BRIDGE_WORKSPACE')
    if override:
        selected = Path(override).expanduser()
        if not selected.is_absolute():
            raise ValueError('CLAUDE_VM_BRIDGE_WORKSPACE must be an absolute external path')
    else:
        checkout = source_root.parents[1] if source_root.parts[-2:] == ('build', 'host') else source_root
        base = Path(env['DEVROOT']) if env.get('DEVROOT') else checkout.parent
        selected = base / 'PROJECTS' / WORKSPACE_NAME
    selected = selected.resolve()
    checkout = source_root.parents[1] if source_root.parts[-2:] == ('build', 'host') else source_root
    if selected.is_relative_to(checkout.resolve()):
        raise ValueError('Workspace must be outside the source checkout')
    return selected
