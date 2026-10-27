from claude_session.mcp import dispatch
from tests.relay_base import RelayBase

class TestCase(RelayBase):
    def test_mcp_never_accepts_hidden_role_argument(self):
            with self.assertRaises(ValueError):
                dispatch({'method': 'tools/call', 'params': {'name': 'claude_send', 'arguments': {
                    'session_id': 'session-a', 'binding': self.binding, 'request_id': 'r',
                    'text': 'hello', 'asUser': True}}}, lambda _: self.fail('transport called'))
            tools = dispatch({'method': 'tools/list'}, None)['tools']
            self.assertEqual(len(tools), 10)
