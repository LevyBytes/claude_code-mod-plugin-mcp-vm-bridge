from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_lost_delivery_becomes_unknown_and_late_ack_can_resolve(self):
            self.state.client(self.send())
            self.state.tick(self.tick)
            self.now += 16
            query = {k: v for k, v in self.send(op='request').items() if k not in {'text', 'source'}}
            self.assertEqual(self.acknowledgement(query)['state'], 'unknown')
            self.assertTrue(self.state.client(self.send())['replayed'])
            self.tick['acks'] = [{'request_id': 'request-a', 'state': 'started'}]
            self.assertEqual(self.state.tick(self.tick)['commands'], [])
            self.assertEqual(self.acknowledgement(query)['state'], 'started')
