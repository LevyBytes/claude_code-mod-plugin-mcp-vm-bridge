"""Host transport and CLI for sessions in the explicitly bound Podman container."""
import json
import subprocess

from bridge_runtime.backend import Backend, INSTALL, ROOT, hidden
from .identity import CONTROL_OPS, PREFIXES, detect, validate


def request(body, *, source=None):
    if not isinstance(body, dict) or any(k in body for k in ('source', 'sender', 'prefix', 'role', 'asUser')):
        raise ValueError('Sender/role fields are not model arguments')
    if body.get('op') == 'capabilities':
        try:
            identity = source or detect()
            error = None
        except ValueError as failure:
            identity, error = None, str(failure)
        return {'ok': True, 'protocol': 3, 'source': identity, 'identity_error': error,
                'prefixes': PREFIXES, 'qualification': 'deployment-specific; capabilities are not test evidence',
                'controls': ['send', 'interrupt', 'configure', 'context', 'open'],
                'open_scope': 'right sidebar in existing contained VS Code profile/workspace',
                'open_requires': 'qualified sidebar companion; no Claude editor tabs open'}
    if body.get('op') in CONTROL_OPS:
        source = validate(source or detect())
    if body.get('op') == 'open':
        from .lifecycle import open_session
        return open_session(body, source)
    wire = dict(body)
    if body.get('op') in CONTROL_OPS:
        wire['source'] = source
    config = json.loads(INSTALL.read_text(encoding='utf-8'))
    backend = Backend(config)
    binding = backend.verify()
    result = subprocess.run([*backend.prefix, 'exec', '-i', '--user', '1000:1000',
        binding['id'], 'python3', '-B', '/opt/kaizen/session-tools/guest_client.py'],
        input=json.dumps(wire).encode(), capture_output=True, timeout=15,
        env=backend.env, cwd=ROOT, **hidden())
    if result.returncode not in (0, 1) or not result.stdout:
        raise RuntimeError('Guest session client unavailable')
    return json.loads(result.stdout)

