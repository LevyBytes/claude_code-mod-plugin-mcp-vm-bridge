from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_old_mod_cannot_silently_use_legacy_prefix(self):
            self.tick['snapshot'].pop('protocol')
            self.state.tick(self.tick)
            with self.assertRaisesRegex(ValueError, 'Unsupported mod protocol'):
                self.state.client(self.send())
