"""Qualify the built mod with the bound guest's installed native validator/test kit."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone

from bridge_runtime.backend import Backend, INSTALL, STATE, hidden
from .archive import zip_bytes
from .files import ROOT
from build import outputs
from .generated import differences


def run():
    expected = outputs()
    if differences(ROOT, expected):
        raise ValueError('Generated payload is stale or contains extra files')
    files = {name.removeprefix('build/plugin/'): data for name, data in expected.items()
             if name.startswith('build/plugin/')}
    data = zip_bytes(files)
    digest = hashlib.sha256(data).hexdigest()
    STATE.mkdir(parents=True, exist_ok=True)
    local = STATE / (digest + '.zip')
    local.write_bytes(data)
    backend = Backend(json.loads(INSTALL.read_text()))
    binding = backend.verify()
    guest = '/home/kaizen/.local/state/kaizen-session/check-' + digest + '.zip'
    backend.call(['cp', str(local), binding['id'] + ':' + guest])
    result = subprocess.run([*backend.prefix, 'exec', '-i', '--user', '1000:1000', binding['id'],
        'python3', '-B', '-', guest], input=(ROOT / 'tools/guest_native_check.py').read_bytes(),
        capture_output=True, env=backend.env, timeout=150, **hidden())
    if result.returncode:
        raise RuntimeError('Native checker failed: ' + result.stderr.decode()[-1500:])
    receipt = json.loads(result.stdout)
    receipt['plugin_sha256'] = digest
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = STATE / 'checks' / ('native-' + stamp + '.json')
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': receipt['passed'], 'receipt': str(path)}))
    return receipt
