"""Create or update the bridge MCP entry without changing other user configuration."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .files import ROOT
from .mcp_config import render
from bridge_runtime.paths import STATE, WORKSPACE


def run():
    state = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    path = state / 'config.toml'
    before = path.read_bytes() if path.exists() else b''
    text = render(before.decode('utf-8'), ROOT, sys.executable, WORKSPACE)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    state.mkdir(parents=True, exist_ok=True)
    backup = state / ('config.before-standalone-bridge-' + stamp + '.toml')
    backup.write_bytes(before)
    if (path.read_bytes() if path.exists() else b'') != before:
        raise RuntimeError('Codex config changed during registration')
    temp = path.with_suffix('.bridge.tmp')
    temp.write_text(text, encoding='utf-8', newline='\n')
    os.replace(temp, path)
    receipt = {'entry': 'kaizen_claude_vm', 'cwd': str(ROOT), 'workspace': str(WORKSPACE), 'backup': str(backup)}
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / 'mcp-registration.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))
