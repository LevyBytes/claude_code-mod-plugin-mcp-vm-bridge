"""Route lifecycle requests through the contained VS Code sidebar companion. No prompt."""
import json
import socket
import sys
import uuid
from pathlib import Path


def main():
    body = json.loads(sys.stdin.buffer.read(4097))
    if set(body) - {'mode', 'target_session', 'allow_live'} or body.get('mode') not in {'new', 'resume', 'status'}:
        raise ValueError('Unsupported desktop request')
    if body['mode'] == 'resume':
        target = str(uuid.UUID(body['target_session']))
        if target != body['target_session']:
            raise ValueError('Canonical session UUID required')
        # Avoid silently creating a new session for an absent target.
        transcript = Path('/home/kaizen/.claude/projects/-workspace') / (target + '.jsonl')
        if body.get('allow_live') is not True and (not transcript.is_file() or transcript.is_symlink()):
            raise ValueError('Session is not available in this workspace; no sidebar command invoked')
    elif 'target_session' in body:
        raise ValueError('New session must not include an existing session ID')
    state = Path.home() / '.local/state/kaizen-session'
    config = json.loads((state / 'relay.json').read_text(encoding='utf-8'))
    wire = {'op': body['mode'], 'token': config['token']}
    if 'target_session' in body:
        wire['target_session'] = body['target_session']
    with socket.socket(getattr(socket, 'AF_UNIX'), socket.SOCK_STREAM) as client:
        client.settimeout(12)
        client.connect(str(state / 'sidebar.sock'))
        client.sendall((json.dumps(wire) + '\n').encode())
        response = bytearray()
        while b'\n' not in response:
            chunk = client.recv(4096)
            if not chunk or len(response) + len(chunk) > 16384:
                raise ValueError('Incomplete or oversized sidebar response')
            response.extend(chunk)
    print(json.dumps(json.loads(response)))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(json.dumps({'ok': False, 'error': str(error)[:500]}))
        raise SystemExit(1)
