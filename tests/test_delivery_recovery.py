"""Fault recovery must preserve acknowledgements and never redispatch a completed model prompt."""
import copy
from tests.relay_base import RelayBase


class DeliveryRecoveryTests(RelayBase):
    def test_lost_response_replays_same_batch_without_duplicate_events_or_new_commands(self):
        self.state.client(self.send())
        batch = {**self.tick, 'batch': 1, 'events': [{'kind': 'first'}]}
        first = self.state.tick(batch)
        commands = first['commands']
        assert isinstance(commands, list)
        self.assertEqual(len(commands), 1)
        self.assertEqual(self.state.tick(copy.deepcopy(batch)), first)
        events = self.state.client({'op': 'events', 'session_id': 'session-a'})['events']
        assert isinstance(events, list)
        self.assertEqual(len(events), 1)
        with self.assertRaisesRegex(ValueError, 'changed observation'):
            self.state.tick({**batch, 'events': [{'kind': 'changed'}]})
        self.now += 16
        query = {k: v for k, v in self.send(op='request').items() if k not in {'text', 'source'}}
        self.assertEqual(self.acknowledgement(query)['state'], 'unknown')
        ack = {**self.tick, 'batch': 2, 'acks': [{'request_id': 'request-a', 'state': 'started'}]}
        self.state.tick(ack)
        self.assertEqual(self.state.tick(ack)['commands'], [])
        self.assertEqual(self.acknowledgement(query)['state'], 'started')
        self.assertEqual(self.state.client(self.send(request_id='next'))['state'], 'queued')
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.state.tick(batch)

    def test_invalid_batch_does_not_claim_a_session_or_downgrade_delivery(self):
        with self.assertRaises(ValueError):
            self.state.tick({**self.tick, 'session_id': 'bad', 'acks': [{'request_id': 'bad', 'state': 'owner'}]})
        self.assertNotIn('bad', self.state.sessions)
        self.state.tick({**self.tick, 'batch': 1})
        with self.assertRaisesRegex(ValueError, 'downgrade'):
            self.state.tick(self.tick)
