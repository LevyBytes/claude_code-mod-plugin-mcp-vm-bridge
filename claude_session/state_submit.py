"""Validated controls, replay barriers and idle checks."""
import re
try:
    from .protocol import fields, identifier
except ImportError:
    from protocol import fields, identifier
try:
    from .identity import validate as validate_source
except ImportError:
    from identity import validate as validate_source

def submit(self, session, data):
        op = data['op']
        extra = {'send': ('text',), 'interrupt': ('turn_id',),
                 'configure': ('model', 'effort'), 'context': ('detail',)}[op]
        required = ('op', 'session_id', 'binding', 'request_id', 'source', *extra)
        fields(data, required)
        validate_source(data['source'])
        if session['snapshot'].get('protocol') != 3:
            raise ValueError('Unsupported mod protocol; open a session with the updated plugin before controlling it')
        if data['binding'] != session['binding']:
            raise ValueError('Session binding changed; inspect it again')
        rid = identifier(data['request_id'])
        if data['op'] == 'send':
            if not isinstance(data['text'], str) or not data['text'].strip() or len(data['text']) > 16000:
                raise ValueError('Message must contain 1-16000 characters')
        elif op == 'interrupt':
            identifier(data['turn_id'])
        elif op == 'configure':
            if (not isinstance(data['model'], str) or
                    not re.fullmatch(r'claude-[a-z0-9.-]+(?:\[1m\])?', data['model']) or
                    len(data['model']) > 128 or data['effort'] not in {'low', 'medium', 'high', 'xhigh', 'max'}):
                raise ValueError('Explicit Claude model ID and supported effort level required')
        elif op == 'context' and data['detail'] not in {'summary', 'full'}:
            raise ValueError('Context detail must be summary or full')
        body = dict(data)
        previous = self.ledger.get(session['binding'], rid)
        if previous is not None:
            if previous['body'] != body:
                raise ValueError('Request ID reused with different content')
            return {'request_id': rid, 'state': previous['state'], 'replayed': True}
        if self.clock() - session['seen'] >= 10:
            raise ValueError('Session disconnected; no request submitted')
        pending = self.ledger.pending(session['binding'])
        queue_limit, pending_limit = (16, 264) if op == 'interrupt' else (8, 256)
        if len(pending) >= pending_limit or len(session['queue']) >= queue_limit:
            raise ValueError('Active request capacity reached')
        if op in {'send', 'configure'} and (session['snapshot'].get('state') != 'idle' or any(
                r['state'] in {'queued', 'dispatched', 'unknown'} and r['body']['op'] in {'send', 'configure'}
                for r in pending)):
            raise ValueError('Session busy; wait or explicitly interrupt its current turn')
        if data['op'] == 'interrupt' and data['turn_id'] != session['snapshot'].get('turn_id'):
            raise ValueError('Turn changed; no interrupt submitted')
        self.ledger.put(session['binding'], rid, {'body': body, 'state': 'queued'})
        if op == 'interrupt':
            session['queue'].appendleft(rid)
        else:
            session['queue'].append(rid)
        return {'request_id': rid, 'state': 'queued', 'replayed': False}
