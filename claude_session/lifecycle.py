"""Host-owned, idempotent GUI launch receipts; verify registered identity before returning it."""
import json
import subprocess
import time
import uuid

from bridge_runtime.backend import Backend, INSTALL, STATE, atomic, hidden
from .state import fields, identifier


def select_opened(before, after, mode, target=None):
    candidates = [s for s in after if s.get('connected') and 'vscode' in s['snapshot'].get('surfaces', [])
                  and s['snapshot'].get('cwd') == '/workspace'
                  and (s['session_id'] == target if mode == 'resume' else s['session_id'] not in before)]
    return candidates[0] if len(candidates) == 1 else None


def open_session(body, source):
    from .host import request
    fields(body, ('op', 'mode', 'request_id'), ('target_session',))
    rid = identifier(body['request_id'])
    if body['mode'] not in {'new', 'resume'}:
        raise ValueError('Mode must be new or resume')
    if body['mode'] == 'resume':
        if str(uuid.UUID(body.get('target_session', ''))) != body['target_session']:
            raise ValueError('Canonical session UUID required')
    elif 'target_session' in body:
        raise ValueError('New session must not supply a target')
    directory = STATE / 'session-open'
    directory.mkdir(exist_ok=True)
    path = directory / (rid + '.json')
    if path.exists():
        previous = json.loads(path.read_text(encoding='utf-8'))
        if previous['body'] != body or previous['source'] != source:
            raise ValueError('Open request ID reused with different content or sender')
        return previous['result']
    observed = request({'op': 'sessions'})
    if not observed.get('ok'):
        return observed
    if any(s['connected'] and s['snapshot'].get('state') != 'idle' for s in observed['sessions']):
        return {'ok': False, 'error': 'A live session is not idle; sidebar switch refused'}
    before = {s['session_id'] for s in observed['sessions']}
    receipt = {'body': body, 'source': source, 'result': {
        'ok': False, 'state': 'unknown', 'error': 'Open outcome unknown; do not repeat with a new request ID'}}
    # Exclusive create is the replay barrier, written before issuing the external action.
    with path.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle)
    backend = Backend(json.loads(INSTALL.read_text(encoding='utf-8')))
    binding = backend.verify()
    payload = {k: body[k] for k in ('mode', 'target_session') if k in body}
    if body['mode'] == 'resume':
        payload['allow_live'] = select_opened(set(), observed['sessions'], 'resume', body['target_session']) is not None
    result = subprocess.run([*backend.prefix, 'exec', '-i', '--user', '1000:1000', binding['id'],
        'python3', '-B', '/opt/kaizen/session-tools/guest_desktop.py'], input=json.dumps(payload).encode(),
        env=backend.env, capture_output=True, timeout=20, **hidden())
    launched = json.loads(result.stdout)
    if not launched.get('ok'):
        receipt['result'] = launched
    else:
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            observed = request({'op': 'sessions'})
            selected = select_opened(before, observed.get('sessions', []), body['mode'], body.get('target_session'))
            if selected is not None:
                receipt['result'] = {'ok': True, 'state': 'opened', 'surface': 'sidebar',
                                     'session': selected, 'model_prompts_sent': 0}
                break
            time.sleep(0.5)
    atomic(path, receipt)
    return receipt['result']
