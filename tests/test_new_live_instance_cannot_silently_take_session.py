from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_new_live_instance_cannot_silently_take_session(self):
            self.tick['instance_id'] = 'instance-b'
            with self.assertRaises(ValueError):
                self.state.tick(self.tick)
            self.now += 11
            self.assertNotEqual(self.binding, self.state.tick(self.tick)['binding'])
