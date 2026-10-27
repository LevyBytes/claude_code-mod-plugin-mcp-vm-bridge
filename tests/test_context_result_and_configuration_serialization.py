from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_context_result_and_configuration_serialization(self):
            config = {k: v for k, v in self.send(op='configure', model='claude-opus-5-5', effort='xhigh').items()
                      if k != 'text'}
            self.state.client(config)
            with self.assertRaises(ValueError):
                self.state.client(self.send(request_id='other'))
            self.state.tick(self.tick)
            self.tick['acks'] = [{'request_id': 'request-a', 'state': 'completed', 'result': {'effort': 'xhigh'}}]
            self.state.tick(self.tick)
            query = {'op': 'request', 'session_id': 'session-a', 'binding': self.binding, 'request_id': 'request-a'}
            self.assertEqual(self.acknowledgement(query)['result']['effort'], 'xhigh')
            values = self.send(op='context', request_id='ctx', detail='summary')
            context = {k: v for k, v in values.items() if k != 'text'}
            self.assertEqual(self.state.client(context)['state'], 'queued')
