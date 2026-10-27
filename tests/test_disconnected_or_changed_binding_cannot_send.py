from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_disconnected_or_changed_binding_cannot_send(self):
            with self.assertRaises(ValueError):
                self.state.client(self.send(binding='old-instance'))
            self.now += 11
            with self.assertRaises(ValueError):
                self.state.client(self.send())
