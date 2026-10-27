"""Completed replay evidence survives reopening the relay's own journal."""
import tempfile
import unittest
from pathlib import Path
from bridge_runtime.paths import STATE
from claude_session.request_ledger import RequestLedger


class RequestJournalTests(unittest.TestCase):
    def test_reopen_preserves_terminal_result_without_consuming_active_capacity(self):
        scratch = STATE / 'tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            path = Path(temp) / 'requests.sqlite3'
            assert path.resolve().is_relative_to(scratch.resolve())
            first = RequestLedger(path)
            try:
                first.put('binding-a', 'request-a', {'state': 'completed', 'result': 'Unicode ✓'})
            finally:
                first.close()
            second = RequestLedger(path)
            try:
                row = second.get('binding-a', 'request-a')
                assert isinstance(row, dict)
                self.assertEqual(row['result'], 'Unicode ✓')
                self.assertEqual(second.pending('binding-a'), [])
                self.assertIsNone(second.get('new-binding', 'request-a'))
            finally:
                second.close()
