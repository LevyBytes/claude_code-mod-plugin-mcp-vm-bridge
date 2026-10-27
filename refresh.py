"""Activate a published update in the observed-idle contained editor; no model submission."""
import json
import subprocess

from bridge_runtime.backend import Backend, INSTALL, hidden
from claude_session.host import request
from tools.files import ROOT

if __name__ == '__main__':
    sessions = request({'op': 'sessions'})
    if not sessions.get('ok') or any(s['connected'] and s['snapshot'].get('state') != 'idle'
                                   for s in sessions['sessions']):
        raise SystemExit('Refusing activation while an observed session is not idle')
    backend = Backend(json.loads(INSTALL.read_text()))
    binding = backend.verify()
    result = subprocess.run([*backend.prefix, 'exec', '-i', '--user', '1000:1000', binding['id'],
        'python3', '-B', '-'], input=(ROOT / 'tools/guest_refresh.py').read_bytes(),
        capture_output=True, env=backend.env, timeout=35, **hidden())
    if result.returncode:
        raise SystemExit('Activation failed: ' + result.stderr.decode()[-1000:])
    print(result.stdout.decode())
