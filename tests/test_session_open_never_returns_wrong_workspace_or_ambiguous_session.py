import unittest
from claude_session.lifecycle import select_opened

class TestCase(unittest.TestCase):
    def test_session_open_never_returns_wrong_workspace_or_ambiguous_session(self):
            def row(sid, cwd='/workspace'):
                return {'session_id': sid, 'connected': True, 'snapshot': {'cwd': cwd, 'surfaces': ['vscode']}}
            self.assertIsNone(select_opened({'old'}, [row('old')], 'new'))
            self.assertIsNone(select_opened({'old'}, [row('a'), row('b')], 'new'))
            self.assertIsNone(select_opened(set(), [row('a', '/other')], 'new'))
            selected = select_opened({'old'}, [row('old'), row('a')], 'new')
            assert selected is not None
            self.assertEqual(selected['session_id'], 'a')
            self.assertIsNone(select_opened(set(), [row('a')], 'resume', 'missing'))
