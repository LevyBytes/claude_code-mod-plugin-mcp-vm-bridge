"""Long sessions and stale registrations cannot permanently exhaust relay capacity."""
from tests.relay_base import RelayBase


class CapacityLifecycleTests(RelayBase):
    def test_1024_completed_requests_retain_replay_protection_without_consuming_slots(self):
        first = None
        for number in range(1024):
            body = self.send(op='context', request_id='r' + str(number), detail='summary')
            body.pop('text')
            first = body if first is None else first
            self.state.client(body)
            self.state.tick(self.tick)
            self.state.tick({**self.tick, 'acks': [{'request_id': body['request_id'], 'state': 'completed'}]})
        self.assertEqual(len(self.state.ledger.pending(self.binding)), 0)
        self.assertEqual(self.state.client(first)['state'], 'completed')
        self.assertTrue(self.state.client(first)['replayed'])
        self.assertEqual(self.state.client(self.send())['state'], 'queued')

    def test_stale_registrations_retire_but_live_ones_are_preserved(self):
        for number in range(1, 16):
            self.state.tick({**self.tick, 'session_id': 's' + str(number)})
        with self.assertRaisesRegex(ValueError, 'Active session capacity'):
            self.state.tick({**self.tick, 'session_id': 'seventeenth'})
        self.now += 11
        self.state.tick({**self.tick, 'session_id': 'seventeenth'})
        self.assertEqual(len(self.state.sessions), 16)
        new = self.state.tick(self.tick)
        self.assertNotEqual(new['binding'], self.binding)
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            self.state.client(self.send())

    def test_interrupt_has_reserved_queue_capacity(self):
        for number in range(8):
            body = self.send(op='context', request_id='r' + str(number), detail='summary')
            body.pop('text')
            self.state.client(body)
        self.state.sessions['session-a']['snapshot'].update(state='working', turn_id='turn-a')
        stop = self.send(op='interrupt', request_id='stop', turn_id='turn-a')
        stop.pop('text')
        self.assertEqual(self.state.client(stop)['state'], 'queued')
        commands = self.state.tick(self.tick)['commands']
        self.assertEqual(commands[0]['op'], 'interrupt')
