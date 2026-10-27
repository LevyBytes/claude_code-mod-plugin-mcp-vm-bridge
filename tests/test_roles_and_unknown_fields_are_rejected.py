from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_roles_and_unknown_fields_are_rejected(self):
            for change in ({'asUser': True}, {'prefix': ''}, {'op': 'approve'}, {'role': 'owner'}):
                with self.assertRaises(ValueError):
                    self.state.client(self.send(**change))
