"""Protect the source/workspace boundary and release contents."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from bridge_runtime.paths import ROOT, STATE, WORKSPACE
from bridge_runtime.workspace import resolve_workspace
from build import outputs
from tools.files import LOCAL_FOLDED, source_files


class WorkspaceLayoutTests(unittest.TestCase):
    def test_runtime_defaults_and_override_stay_outside_checkout(self):
        dev = WORKSPACE.parent.parent
        expected = dev / 'PROJECTS/Kaizen_claude_code_mod_orchestration_vm_bridge'
        self.assertEqual(resolve_workspace(ROOT, {'DEVROOT': str(dev)}), expected)
        self.assertEqual(resolve_workspace(ROOT / 'build/host', {'DEVROOT': str(dev)}), expected)
        self.assertEqual(resolve_workspace(ROOT, {'CLAUDE_VM_BRIDGE_WORKSPACE': str(expected)}), expected)
        for value in ('relative-path', str(ROOT / 'runtime')):
            with self.assertRaises(ValueError):
                resolve_workspace(ROOT, {'CLAUDE_VM_BRIDGE_WORKSPACE': value})

    def test_source_inventory_refuses_local_material(self):
        (STATE / 'tmp').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=STATE / 'tmp') as temp:
            root = Path(temp)
            (root / 'bridge.py').write_text('pass\n')
            (root / '.git').write_text('gitdir: unrelated-location\n')
            self.assertEqual([p.name for p in source_files(root)], ['bridge.py'])
            for name in ('AGENTS.md', 'STATUS.md', 'provenance.json'):
                bad = root / name
                bad.write_text('local material\n')
                with self.assertRaises(ValueError):
                    list(source_files(root))
                bad.unlink()
            (root / 'mod').mkdir()
            (root / 'mod/agents.md').write_text('local material\n')
            with self.assertRaises(ValueError):
                list(source_files(root))

    def test_archives_only_contain_public_files_and_apache_notices(self):
        files = outputs()
        license_text, notice = (ROOT / 'LICENSE').read_bytes(), (ROOT / 'NOTICE').read_bytes()
        self.assertIn(b'Apache License', license_text)
        self.assertIn(b'LevyBytes - David Levy', notice)
        for target in ('build/plugin/', 'build/host/'):
            self.assertEqual(files[target + 'LICENSE'], license_text)
            self.assertEqual(files[target + 'NOTICE'], notice)
        with zipfile.ZipFile(io.BytesIO(files['dist/claude-vm-bridge-0.3.0.zip'])) as archive:
            for name in archive.namelist():
                self.assertFalse(set(part.casefold() for part in Path(name).parts) & LOCAL_FOLDED, name)
            self.assertEqual(archive.read('NOTICE'), notice)
        with zipfile.ZipFile(io.BytesIO(files['build/claude-sidebar-bridge.vsix'])) as archive:
            self.assertEqual(archive.read('extension/LICENSE.txt'), license_text)
            self.assertEqual(archive.read('extension/NOTICE.txt'), notice)
            manifest = json.loads(archive.read('extension/package.json'))
            self.assertEqual(manifest['license'], 'Apache-2.0')
