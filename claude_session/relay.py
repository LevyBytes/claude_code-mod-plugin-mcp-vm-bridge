"""Private loopback relay inside the container; no provider credentials or shell API."""
import argparse
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if __package__:
    from .state import State
else:
    from state import State

PORT = 39086
CONFIG = Path('/home/kaizen/.local/state/kaizen-session/relay.json')


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, state, token):
        self.state, self.token = state, token
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server: Server

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_):
        pass

    def do_POST(self):
        if not secrets.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + self.server.token):
            self.respond(403, {'ok': False, 'error': 'Authentication required'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 262144 or self.headers.get('Transfer-Encoding'):
                raise ValueError('Invalid body length')
            data = json.loads(self.rfile.read(length))
            if self.path == '/mod':
                result = self.server.state.tick(data)
            elif self.path == '/client':
                result = self.server.state.client(data)
            else:
                raise ValueError('Unsupported endpoint')
            self.respond(200, {'ok': True, **result})
        except (ValueError, TypeError, KeyError) as error:
            self.respond(400, {'ok': False, 'error': str(error)[:1000]})

    def respond(self, code, value):
        body = json.dumps(value, ensure_ascii=True).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--config', type=Path, default=CONFIG)
    args = parser.parse_args()
    os.umask(0o077)
    args.config.parent.mkdir(parents=True, exist_ok=True)
    state = State(ledger_path=args.config.parent / 'requests.sqlite3')
    token = secrets.token_urlsafe(32)
    server = Server(('127.0.0.1', PORT), state, token)
    args.config.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.config.with_suffix('.tmp')
    temporary.write_text(json.dumps({'url': f'http://127.0.0.1:{PORT}', 'token': token,
                                     'epoch': state.epoch, 'pid': os.getpid()}), encoding='utf-8')
    os.replace(temporary, args.config)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        state.ledger.close()


if __name__ == '__main__':
    main()
