from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_ack_cannot_promote_to_owner_or_invent_request(self):
            self.state.client(self.send())
            self.state.tick(self.tick)
            self.tick['acks'] = [{'request_id': 'request-a', 'state': 'approved'}]
            with self.assertRaises(ValueError):
                self.state.tick(self.tick)
            self.tick['acks'] = [{'request_id': 'request-a', 'state': 'started'}]
            self.state.tick(self.tick)
            query = {k: v for k, v in self.send(op='request').items() if k not in {'text', 'source'}}
            self.assertEqual(self.acknowledgement(query)['state'], 'started')
