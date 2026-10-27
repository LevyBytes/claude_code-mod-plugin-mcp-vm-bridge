from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_duplicate_does_not_dispatch_twice(self):
            self.state.client(self.send())
            self.assertTrue(self.state.client(self.send())['replayed'])
            self.assertEqual(len(self.state.tick(self.tick)['commands']), 1)
            self.assertEqual(self.state.tick(self.tick)['commands'], [])
            with self.assertRaises(ValueError):
                self.state.client(self.send(text='Different work'))
