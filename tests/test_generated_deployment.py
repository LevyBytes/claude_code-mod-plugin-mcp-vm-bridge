"""Exact inventory and frozen payload regressions."""
from tools import deployment
from tools.generated import differences, publish
from tests.deployment_fixture import DeploymentFixture


class GeneratedDeploymentTests(DeploymentFixture):
    def test_extra_generated_file_fails_check_and_rebuild_removes_it(self):
        stale = self.source / 'build/plugin/hooks/retired.js'
        stale.write_bytes(b'// stale\n')
        self.assertIn('build/plugin/hooks/retired.js', differences(self.source, self.expected))
        with self.assertRaisesRegex(ValueError, 'Generated outputs differ'):
            deployment.plan(self.config)
        publish(self.source, self.expected)
        self.assertFalse(stale.exists())
        self.assertEqual(differences(self.source, self.expected), [])

    def test_deployment_uses_frozen_bytes_and_backs_up_removed_files(self):
        retired = self.roots['mod'] / 'retired.js'
        self.expected['build/plugin/retired.js'] = b'// obsolete managed output\n'
        publish(self.source, self.expected)
        deployment.apply(deployment.plan(self.config))
        del self.expected['build/plugin/retired.js']
        publish(self.source, self.expected)
        plan = deployment.plan(self.config)
        self.assertIn((None, retired), plan)
        (self.source / 'build/plugin/hooks/register.js').write_bytes(b'// unvalidated change\n')
        receipt = deployment.apply(plan)
        self.assertTrue(receipt)
        self.assertEqual((self.roots['mod'] / 'hooks/register.js').read_bytes(), b'// checked\n')
        self.assertFalse(retired.exists())
        with self.assertRaisesRegex(ValueError, 'Generated outputs differ'):
            deployment.plan(self.config)

    def test_unmanaged_destination_file_is_preserved_and_blocks_update(self):
        note = self.roots['mod'] / 'owner-note.txt'
        note.write_bytes(b'preserve this')
        with self.assertRaisesRegex(ValueError, 'Unmanaged deployment files'):
            deployment.plan(self.config)
        self.assertEqual(note.read_bytes(), b'preserve this')
