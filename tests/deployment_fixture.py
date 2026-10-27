"""Isolated mapped-directory fixture; never uses the configured pilot."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bridge_runtime.paths import STATE
from tools import deployment
from tools.generated import publish
from tools.grants import grants


class DeploymentFixture(unittest.TestCase):
    def setUp(self):
        scratch = STATE / 'tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.root = Path(temporary.name).resolve()
        assert self.root.is_relative_to(scratch.resolve())
        self.addCleanup(temporary.cleanup)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.roots = {'guest_tools': self.root / 'target-tools', 'mod': self.root / 'target-mod'}
        for path in self.roots.values():
            path.mkdir()
        self.expected = {'build/host/claude_session/' + name: b'# checked\n' for name in deployment.GUEST_FILES}
        self.expected['build/plugin/hooks/register.js'] = b'// checked\n'
        publish(self.source, self.expected)
        self.config = {'podman': 'unused', 'container_binding': {'id': 'synthetic', 'mounts': [
            {'Type': 'bind', 'Source': '/alias/tools', 'Destination': '/opt/kaizen/session-tools', 'RW': False},
            {'Type': 'bind', 'Source': '/alias/mod', 'Destination': '/opt/kaizen/claude-session-mod', 'RW': False}]},
            'deployment': {key: str(value) for key, value in self.roots.items()}}
        self.config['deployment_bindings'] = grants(self.config, require_binding=False)[1]
        for target, value in (('ROOT', self.source), ('STATE', self.root / 'receipts')):
            patcher = patch.object(deployment, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(deployment, 'outputs', lambda: dict(self.expected))
        patcher.start()
        self.addCleanup(patcher.stop)
