import unittest
from claude_session.runtime_adapter import detect_runtime

class TestCase(unittest.TestCase):
    def test_runtime_metadata_does_not_depend_on_ports_or_model_name(self):
            fixtures = {
                'ollama': {'/api/version': {'version': 'test'}, '/api/tags': {'models': []}},
                'llama.cpp': {'/props': {'default_generation_settings': {}, 'total_slots': 1, 'chat_template': 'test'}},
                'vllm': {'/version': {'version': 'test'}, '/v1/models': {'data': [{'owned_by': 'vllm'}]}},
            }
            for kind, fixture in fixtures.items():
                self.assertEqual(detect_runtime('http://127.0.0.1:23991', lambda p: fixture.get(p, {}))['kind'], kind)
            combined = {**fixtures['ollama'], **fixtures['vllm']}
            for fixture in ({}, combined):
                with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_SENDER_IDENTITY'):
                    detect_runtime('http://127.0.0.1:23991', lambda p: fixture.get(p, {}))
            with self.assertRaises(ValueError):
                detect_runtime('http://user:secret@localhost', lambda _: {})
