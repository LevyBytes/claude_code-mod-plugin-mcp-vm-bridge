"""Preview the approved pilot update; --apply publishes only after conformance and native checks."""
import argparse
import json
import subprocess
import sys

from bridge_runtime.backend import Backend, INSTALL
from claude_session.host import request
from tools.deployment import apply, plan
from tools.bind_instance import qualify
from tools.files import ROOT
from tools.native_check import run as native_check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    config = json.loads(INSTALL.read_text())
    backend = Backend(config)
    backend.verify()
    rows = plan(config)
    print(json.dumps({'files': len(rows), 'apply': args.apply, 'destinations': config['deployment'],
                      'removals': [str(target) for data, target in rows if data is None]}), flush=True)
    if not args.apply:
        return 0
    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'conformance.py')], cwd=ROOT)
    if result.returncode or not native_check()['passed']:
        raise RuntimeError('Update blocked by conformance/native tests')
    sessions = request({'op': 'sessions'})
    if not sessions.get('ok') or any(s['connected'] and s['snapshot'].get('state') != 'idle'
                                   for s in sessions['sessions']):
        raise RuntimeError('Observed sessions must be idle before publishing an update')
    if plan(config) != rows:
        raise RuntimeError('Payload or destinations changed during checks; rebuild and retry')
    if qualify(config)['deployment_bindings'] != config['deployment_bindings']:
        raise RuntimeError('Mapping relationship changed during qualification')
    backend.verify()
    backup = apply(rows)
    print(json.dumps({'published': True, 'rollback': backup,
        'activation': 'Restart the owned relay and reload the idle contained editor to activate new code.',
        'host_editor_changed': False, 'model_prompts_sent': 0}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}), file=sys.stderr)
        raise SystemExit(1)
