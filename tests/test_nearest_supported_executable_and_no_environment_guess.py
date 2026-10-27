import unittest
from claude_session.identity import classify, validate

class TestCase(unittest.TestCase):
    def test_nearest_supported_executable_and_no_environment_guess(self):
            self.assertEqual(classify([{'name': 'python.exe', 'path': 'D:/python.exe'},
                {'name': 'codex.exe', 'path': 'D:/tools/codex.exe'}])['kind'], 'codex')
            for rows in ([], [{'name': 'codex.exe', 'path': 'D:/other.exe'}],
                         [{'name': 'python', 'path': '/usr/bin/python'}]):
                with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_SENDER_IDENTITY'):
                    classify(rows)
            with self.assertRaises(ValueError):
                validate({'kind': 'codex', 'method': 'model_claim'})
