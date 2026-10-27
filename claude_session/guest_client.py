"""Read one JSON request from stdin, call only the fixed guest relay, return JSON."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

CONFIG = Path('/home/kaizen/.local/state/kaizen-session/relay.json')


def main():
    body = sys.stdin.buffer.read(262145)
    if not 0 < len(body) <= 262144:
        raise ValueError('Invalid request length')
    json.loads(body)
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    if config['url'] != 'http://127.0.0.1:39086':
        raise ValueError('Unexpected local relay endpoint')
    request = urllib.request.Request(config['url'] + '/client', data=body,
        headers={'Authorization': 'Bearer ' + config['token'], 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=8) as response:
            result = json.loads(response.read(1048576))
    except urllib.error.HTTPError as error:
        result = json.loads(error.read(4096))
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result.get('ok') else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError):
        print(json.dumps({'ok': False, 'error': 'Local session relay unavailable or invalid'}))
        raise SystemExit(1)
