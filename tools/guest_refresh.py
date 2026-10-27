"""Refresh only the UID-owned relay and exact contained editor profile."""
import json
import os
import signal
import subprocess
import time
from pathlib import Path

state = Path.home() / '.local/state/kaizen-session'
uid = Path('/proc/self').stat().st_uid
config = json.loads((state / 'relay.json').read_text())
relay = Path('/proc') / str(config['pid'])
relay_command = relay.joinpath('cmdline').read_bytes()
if relay.stat().st_uid != uid or b'/opt/kaizen/session-tools/relay.py' not in relay_command:
    raise RuntimeError('Relay ownership/path mismatch')
marker = b'--user-data-dir=/home/kaizen/editor-state/user-data'
editors = []
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit():
        continue
    try:
        raw = proc.joinpath('cmdline').read_bytes()
        if marker in raw and b'--type=' not in raw and proc.stat().st_uid == uid:
            if proc.joinpath('exe').resolve().name == 'code':
                editors.append(proc)
    except OSError:
        pass
if len(editors) != 1:
    raise RuntimeError('Expected one owned contained editor main process')
editor = editors[0]
env = os.environ.copy()
for entry in editor.joinpath('environ').read_bytes().split(bytes([0])):
    key, separator, value = entry.partition(b'=')
    if separator and key in {b'DISPLAY', b'XAUTHORITY', b'XDG_RUNTIME_DIR', b'DBUS_SESSION_BUS_ADDRESS'}:
        env[key.decode()] = value.decode()
env['DONT_PROMPT_WSL_INSTALL'] = '1'
for proc in [editor, relay]:
    os.kill(int(proc.name), signal.SIGTERM)
    for _ in range(100):
        if not proc.exists():
            break
        time.sleep(.1)
    else:
        raise RuntimeError('Owned process did not exit; no duplicate launched')
with (state / 'refresh-relay.log').open('ab') as log:
    subprocess.Popen(['python3', '-B', '/opt/kaizen/session-tools/relay.py'],
        stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
for _ in range(100):
    fresh = json.loads((state / 'relay.json').read_text())
    if fresh['epoch'] != config['epoch']:
        break
    time.sleep(.1)
else:
    raise RuntimeError('New relay did not become ready')
with (state / 'refresh-editor.log').open('ab') as log:
    subprocess.Popen(['/usr/bin/code', '--disable-gpu', '--disable-telemetry', '--disable-updates',
        '--skip-welcome', '--skip-release-notes', marker.decode(),
        '--extensions-dir=/home/kaizen/editor-state/extensions', '/workspace'], env=env,
        stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
print(json.dumps({'refreshed': True, 'host_editor_changed': False, 'old_bindings_invalidated': True}))
