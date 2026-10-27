"""Bound active registrations; retiring a stale registration always changes its binding."""
import uuid
from collections import deque


def session_for(state, sid, instance):
    session = state.sessions.get(sid)
    if session is not None and session['instance'] == instance:
        return session
    if session is not None and state.clock() - session['seen'] < 10:
        raise ValueError('Another live mod instance already owns this session')
    if session is None and len(state.sessions) >= 16:
        stale = [s for s in state.sessions.values() if state.clock() - s['seen'] >= 10]
        if not stale:
            raise ValueError('Active session capacity reached')
        oldest = min(stale, key=lambda s: s['seen'])
        del state.sessions[oldest['id']]
    session = {'id': sid, 'instance': instance, 'binding': state.epoch + ':' + uuid.uuid4().hex,
               'snapshot': {}, 'seen': state.clock(), 'events': deque(maxlen=512),
               'sequence': 0, 'queue': deque(), 'batch': None}
    state.sessions[sid] = session
    return session
