"""Bounded read operations and routing to submission checks."""
try:
    from .protocol import fields, identifier
except ImportError:
    from protocol import fields, identifier

def client(self, data):
        if not isinstance(data, dict):
            raise ValueError('Object required')
        op = data.get('op')
        if op not in {'sessions', 'status', 'events', 'send', 'interrupt', 'request', 'configure', 'context'}:
            raise ValueError('Unsupported operation')
        if op == 'sessions':
            fields(data, ('op',))
            with self.lock:
                return {'sessions': [self.view(s) for s in self.sessions.values()]}
        with self.lock:
            sid = identifier(data.get('session_id'))
            session = self.sessions.get(sid)
            if session is None:
                raise ValueError('Session not registered')
            if op == 'status':
                fields(data, ('op', 'session_id'))
                return self.view(session)
            if op == 'events':
                fields(data, ('op', 'session_id'), ('after',))
                after = data.get('after', 0)
                if type(after) is not int or after < 0 or after > session['sequence']:
                    raise ValueError('Invalid cursor; obtain current session status')
                entries = list(session['events'])
                rows = [r for r in entries if r['cursor'] > after][:64]
                return {'binding': session['binding'], 'events': rows,
                        'cursor': rows[-1]['cursor'] if rows else after,
                        'gap': bool(entries and after < entries[0]['cursor'] - 1)}
            if op == 'request':
                fields(data, ('op', 'session_id', 'binding', 'request_id'))
                if data['binding'] != session['binding']:
                    raise ValueError('Session binding changed')
                row = self.ledger.get(session['binding'], identifier(data['request_id']))
                if row and row['state'] == 'dispatched' and self.clock() - row['dispatched_at'] > 15:
                    row.update(state='unknown', detail='No mod acknowledgement; do not automatically replay')
                    self.ledger.put(session['binding'], data['request_id'], row)
                return {'request': None if row is None else {
                    **{k: row.get(k) for k in ('state', 'detail', 'result')},
                    'source': row['body']['source']}}
            return self.submit(session, data)
