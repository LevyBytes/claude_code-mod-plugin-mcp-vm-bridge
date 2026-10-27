from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_unknown_sender_cannot_queue_and_cannot_change_on_replay(self):
            with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_SENDER_IDENTITY'):
                self.state.client(self.send(source={'kind': 'owner', 'method': 'executable_ancestry'}))
            self.state.client(self.send())
            with self.assertRaises(ValueError):
                self.state.client(self.send(source={'kind': 'ollama', 'method': 'runtime_adapter'}))
