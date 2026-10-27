import unittest
from claude_session.state import State

class RelayBase(unittest.TestCase):
    def acknowledgement(self, query):
        result = self.state.client(query)['request']
        assert isinstance(result, dict), 'Expected an acknowledgement object'
        return result

    def setUp(self):
            self.now = 100
            self.state = State(lambda: self.now)
            self.addCleanup(self.state.ledger.close)
            self.tick = {'session_id': 'session-a', 'instance_id': 'instance-a',
                         'snapshot': {'state': 'idle', 'turn_id': None, 'protocol': 3}, 'events': [], 'acks': []}
            self.binding = self.state.tick(self.tick)['binding']

    def send(self, **changes):
            return {'op': 'send', 'session_id': 'session-a', 'binding': self.binding,
                    'request_id': 'request-a', 'text': 'Inspect only',
                    'source': {'kind': 'codex', 'method': 'executable_ancestry'}, **changes}
