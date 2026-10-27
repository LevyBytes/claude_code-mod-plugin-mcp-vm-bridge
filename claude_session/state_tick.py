"""Deduplicated observations and acknowledgements; commands are returned once per batch."""
try:
    from .session_registry import session_for
    from .tick_validation import validate, replay
except ImportError:
    from session_registry import session_for
    from tick_validation import validate, replay


def tick(self, data):
    validate(data)
    with self.lock:
        session = session_for(self, data['session_id'], data['instance_id'])
        cached, digest = replay(session, data)
        if cached is not None:
            return cached
        session['seen'], session['snapshot'] = self.clock(), data['snapshot']
        for event in data['events']:
            session['sequence'] += 1
            session['events'].append({'cursor': session['sequence'], 'event': event})
        for ack in data['acks']:
            request = self.ledger.get(session['binding'], ack['request_id'])
            if request is not None and request['state'] in {'dispatched', 'unknown'}:
                request.update(state=ack['state'], detail=str(ack.get('detail', ''))[:2000])
                if 'result' in ack:
                    request['result'] = ack['result']
                self.ledger.put(session['binding'], ack['request_id'], request)
        commands = []
        while session['queue'] and len(commands) < 4:
            rid = session['queue'].popleft()
            request = self.ledger.get(session['binding'], rid)
            request.update(state='dispatched', dispatched_at=self.clock())
            self.ledger.put(session['binding'], rid, request)
            commands.append(request['body'])
        reply = {'binding': session['binding'], 'commands': commands}
        if digest is not None:
            reply['batch'] = data['batch']
            session['batch'] = {'number': data['batch'], 'digest': digest, 'reply': reply}
        return reply
