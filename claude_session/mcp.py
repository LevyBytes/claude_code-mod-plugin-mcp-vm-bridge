"""Small stdio MCP facade; no additional listener or owner-approval operations."""
import json
import sys

BASE = {'session_id': {'type': 'string'}}
BINDING = {**BASE, 'binding': {'type': 'string'}, 'request_id': {'type': 'string'}}
SPECS = {
    'capabilities': ({}, [], 'Read supported controls and automatically detected sender; no inference.'),
    'sessions': ({}, [], 'List contained Claude sessions and their current binding/status.'),
    'status': (BASE, ['session_id'], 'Read observed session state and available context usage; no inference.'),
    'events': ({**BASE, 'after': {'type': 'integer', 'minimum': 0}}, ['session_id'],
               'Read bounded session events after a cursor; check gap before interpreting completeness.'),
    'send': ({**BINDING, 'text': {'type': 'string', 'minLength': 1, 'maxLength': 16000}},
             [*BINDING, 'text'], 'Submit an automatically attributed assistant request. May start billable inference.'),
    'interrupt': ({**BINDING, 'turn_id': {'type': 'string'}}, [*BINDING, 'turn_id'],
                  'Request interruption of the exact current turn; does not stop the VM or prove tool cleanup.'),
    'request': (BINDING, [*BINDING], 'Inspect acknowledgement of an existing request without replaying it.'),
    'configure': ({**BINDING, 'model': {'type': 'string'}, 'effort': {
        'type': 'string', 'enum': ['low', 'medium', 'high', 'xhigh', 'max']}},
        [*BINDING, 'model', 'effort'], 'Set session-local main-request model/effort overrides while idle.'),
    'context': ({**BINDING, 'detail': {'type': 'string', 'enum': ['summary', 'full']}},
        [*BINDING, 'detail'], 'Request context breakdown; inspect claude_request. Full uses token counting.'),
    'open': ({'mode': {'type': 'string', 'enum': ['new', 'resume']}, 'request_id': {'type': 'string'},
              'target_session': {'type': 'string'}}, ['mode', 'request_id'],
             'Open a new or prior conversation in the contained RIGHT SIDEBAR. Requires no Claude editor tabs. '
             'Return verified session identity or an explicit unresolved result; never retry an uncertain open.'),
}


def dispatch(message, transport):
    method, params = message.get('method'), message.get('params', {})
    if method == 'initialize':
        return {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}},
                'serverInfo': {'name': 'kaizen-contained-claude', 'version': '0.3.0'}}
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return {'tools': [{'name': 'claude_' + name, 'description': spec[2], 'inputSchema': {
            'type': 'object', 'properties': spec[0], 'required': spec[1], 'additionalProperties': False}}
            for name, spec in SPECS.items()]}
    if method == 'tools/call':
        name = params.get('name', '').removeprefix('claude_')
        if name not in SPECS or params.get('name') != 'claude_' + name:
            raise ValueError('Unknown tool')
        args = params.get('arguments', {})
        spec = SPECS[name]
        if not isinstance(args, dict) or args.keys() - spec[0].keys() or not set(spec[1]) <= args.keys():
            raise ValueError('Missing or unsupported arguments')
        try:
            result = transport({'op': name, **args})
        except ValueError as error:
            result = {'ok': False, 'error': str(error)}
        return {'content': [{'type': 'text', 'text': json.dumps(result)}], 'isError': not result.get('ok')}
    raise ValueError('Unsupported method')


def serve(transport):
    initialized = False
    while True:
        raw = sys.stdin.buffer.readline(262146)
        if not raw:
            return 0
        if len(raw) > 262144:
            return 2
        message = None
        try:
            message = json.loads(raw)
            if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
                raise ValueError('JSON-RPC object required')
            if 'id' not in message:
                continue
            if message.get('method') == 'initialize':
                if initialized:
                    raise ValueError('Connection is already initialized')
                initialized = True
            elif not initialized:
                raise ValueError('Initialize before calling tools')
            answer = {'jsonrpc': '2.0', 'id': message['id'], 'result': dispatch(message, transport)}
        except Exception:
            answer = {'jsonrpc': '2.0', 'id': message.get('id') if isinstance(message, dict) else None,
                      'error': {'code': -32602, 'message': 'Request failed; inspect session state before retrying'}}
        print(json.dumps(answer), flush=True)
