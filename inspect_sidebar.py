"""Read the contained sidebar companion's build qualification; no model prompt or editor action."""
import json
import subprocess

from bridge_runtime.backend import Backend, INSTALL, hidden


def main():
    backend = Backend(json.loads(INSTALL.read_text(encoding='utf-8')))
    binding = backend.verify()
    result = subprocess.run([*backend.prefix, 'exec', '-i', '--user', '1000:1000', binding['id'],
        'python3', '-B', '/opt/kaizen/session-tools/guest_desktop.py'],
        input=b'{"mode":"status"}', capture_output=True, env=backend.env, timeout=20, **hidden())
    response = json.loads(result.stdout)
    print(json.dumps(response))
    return 0 if response.get('ok') and response.get('qualified') else 1


if __name__ == '__main__':
    raise SystemExit(main())
