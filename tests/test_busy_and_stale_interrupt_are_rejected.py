from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_busy_and_stale_interrupt_are_rejected(self):
            self.tick['snapshot'] = {'state': 'working', 'turn_id': 'turn-a', 'protocol': 3}
            self.state.tick(self.tick)
            with self.assertRaises(ValueError):
                self.state.client(self.send())
            interrupt = {'op': 'interrupt', 'session_id': 'session-a', 'binding': self.binding,
                         'request_id': 'request-b', 'turn_id': 'turn-b', 'source': self.send()['source']}
            with self.assertRaises(ValueError):
                self.state.client(interrupt)
            interrupt['turn_id'] = 'turn-a'
            self.assertEqual(self.state.client(interrupt)['state'], 'queued')
