"""State composition; guest observations never confer owner authority."""
import threading
import time
import uuid
try:
    from .state_tick import tick
    from .state_client import client
    from .state_submit import submit
    from .request_ledger import RequestLedger
    from .protocol import fields as fields, identifier as identifier
except ImportError:
    from state_tick import tick
    from state_client import client
    from state_submit import submit
    from request_ledger import RequestLedger
    from protocol import fields as fields, identifier as identifier


class State:
    tick = tick
    client = client
    submit = submit

    def __init__(self, clock=time.monotonic, ledger_path=':memory:'):
        self.clock, self.epoch = clock, uuid.uuid4().hex
        self.lock, self.sessions = threading.RLock(), {}
        self.ledger = RequestLedger(ledger_path)

    def view(self, session):
        age = max(0, self.clock() - session['seen'])
        return {'session_id': session['id'], 'binding': session['binding'],
                'age_seconds': round(age, 2), 'connected': age < 10,
                'snapshot': session['snapshot'], 'source': 'guest_mod'}
