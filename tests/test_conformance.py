"""Check the gate's actual failure boundaries."""
import tempfile
import unittest
from pathlib import Path

from bridge_runtime.paths import STATE
from tools.size_gate import check_file


class ConformanceTests(unittest.TestCase):
    def test_physical_lines_columns_crlf_and_nul(self):
        scratch = STATE / 'tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            path = Path(directory) / 'example.py'
            path.write_bytes(b'#\n' * 100)
            self.assertEqual(check_file(path), [])
            for raw in (b'#\n' * 101, b'#' * 121 + b'\n', b'#\r\n', b'#\x00\n'):
                path.write_bytes(raw)
                self.assertTrue(check_file(path), repr(raw[:20]))
