import unittest
from claude_session.runtime_adapter import RuntimeConnection

class TestCase(unittest.TestCase):
    def test_local_adapter_prevents_sender_field_in_generated_arguments(self):
            fixture = {'/api/version': {'version': 'test'}, '/api/tags': {'models': []}}
            calls = []
            connection = RuntimeConnection('http://localhost:23991',
                transport=lambda body, **kw: calls.append((body, kw)), get_json=lambda p: fixture.get(p, {}))
            connection.request({'op': 'send', 'text': 'test'})
            self.assertEqual(calls[0][1]['source']['kind'], 'ollama')
            with self.assertRaises(ValueError):
                connection.request({'op': 'send', 'source': {'kind': 'codex'}})
