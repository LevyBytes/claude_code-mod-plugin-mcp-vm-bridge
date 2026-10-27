"""Human CLI and stdio MCP entrypoint."""
import argparse
import json
import subprocess
from pathlib import Path
from .host import request
from .identity import CONTROL_OPS, UNSUPPORTED, detect

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('operation', choices=['sessions', 'status', 'events', 'send', 'interrupt', 'request',
                                             'configure', 'context', 'open', 'capabilities', 'mcp'])
    parser.add_argument('--session', dest='session_id')
    parser.add_argument('--binding')
    parser.add_argument('--id', dest='request_id')
    parser.add_argument('--message-file', type=Path)
    parser.add_argument('--turn', dest='turn_id')
    parser.add_argument('--after', type=int)
    parser.add_argument('--model')
    parser.add_argument('--effort', choices=['low', 'medium', 'high', 'xhigh', 'max'])
    parser.add_argument('--detail', choices=['summary', 'full'])
    parser.add_argument('--mode', choices=['new', 'resume'])
    parser.add_argument('--target-session', dest='target_session')
    args = parser.parse_args(argv)
    if args.operation == 'mcp':
        from .mcp import serve
        try:
            connection_source = detect()
        except ValueError:
            connection_source = None
        def connection_request(body):
            if body.get('op') in CONTROL_OPS and connection_source is None:
                raise ValueError(UNSUPPORTED)
            return request(body, source=connection_source)
        return serve(connection_request)
    body = {'op': args.operation}
    for key in ('session_id', 'binding', 'request_id', 'turn_id', 'after', 'model', 'effort', 'detail', 'mode',
                'target_session'):
        if getattr(args, key) is not None:
            body[key] = getattr(args, key)
    if args.message_file:
        if args.message_file.stat().st_size > 65536:
            parser.error('Message file exceeds 64 KiB')
        body['text'] = args.message_file.read_text(encoding='utf-8')
    try:
        value = request(body)
    except ValueError as error:
        value = {'ok': False, 'error': str(error)}
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        value = {'ok': False, 'error': 'Transport unavailable; outcome unknown. Inspect before retrying.'}
    print(json.dumps(value, ensure_ascii=True))
    return 0 if value.get('ok') else 1
