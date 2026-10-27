"""Fresh registration and custom workspace routing must not require pre-existing provider entries."""
import tomllib
import unittest
from pathlib import PurePosixPath as Path
from tools.mcp_config import render


class RegistrationTests(unittest.TestCase):
    def test_new_entry_with_empty_or_existing_other_settings(self):
        for before in ('', 'model = "unchanged"\n[mcp_servers.other]\ncommand = "keep"\n'):
            text = render(before, Path('/source'), Path('/python'), Path('/external'))
            result = tomllib.loads(text)
            server = result['mcp_servers'].pop('kaizen_claude_vm')
            self.assertEqual(server['env']['CLAUDE_VM_BRIDGE_WORKSPACE'], '/external')
            self.assertEqual(server['args'], ['-B', '-X', 'utf8', '/source/bridge.py', 'mcp'])
            original = tomllib.loads(before)
            self.assertEqual(result.get('model'), original.get('model'))
            self.assertEqual(result['mcp_servers'], original.get('mcp_servers', {}))

    def test_repoint_removes_old_entry_subtables_only(self):
        before = ('[mcp_servers.kaizen_claude_vm]\ncommand = "old"\n'
                  '[mcp_servers.kaizen_claude_vm.env]\nOLD = "value"\n'
                  '[mcp_servers.other]\ncommand = "keep"\n')
        result = tomllib.loads(render(before, Path('/source'), '/python', '/external'))
        self.assertEqual(result['mcp_servers']['other']['command'], 'keep')
        self.assertEqual(result['mcp_servers']['kaizen_claude_vm']['env'],
                         {'CLAUDE_VM_BRIDGE_WORKSPACE': '/external'})
