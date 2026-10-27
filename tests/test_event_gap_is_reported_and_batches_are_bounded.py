from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_event_gap_is_reported_and_batches_are_bounded(self):
            for n in range(10):
                self.tick['events'] = [{'kind': 'text', 'text': str(n)} for _ in range(64)]
                self.state.tick(self.tick)
            result = self.state.client({'op': 'events', 'session_id': 'session-a', 'after': 0})
            self.assertTrue(result['gap'])
            rows = result['events']
            assert isinstance(rows, list)
            self.assertEqual(len(rows), 64)
