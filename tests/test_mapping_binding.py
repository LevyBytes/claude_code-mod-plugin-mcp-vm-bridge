"""Destination checks and live-mapping proof logic run against local synthetic folders."""
import copy
from tools import deployment
from tools.bind_instance import qualify
from tests.deployment_fixture import DeploymentFixture


class MappingBindingTests(DeploymentFixture):
    def test_mismatched_relative_and_missing_binding_fail_before_deployment(self):
        other = self.root / 'unmapped'
        other.mkdir()
        for bad in (str(other), 'relative'):
            config = copy.deepcopy(self.config)
            config['deployment']['mod'] = bad
            with self.assertRaises(ValueError):
                deployment.plan(config)
        config = copy.deepcopy(self.config)
        config.pop('deployment_bindings')
        with self.assertRaisesRegex(ValueError, 'qualified mounts'):
            deployment.plan(config)
        config = copy.deepcopy(self.config)
        config['container_binding']['mounts'][0]['Source'] = '/different'
        with self.assertRaisesRegex(ValueError, 'qualified mounts'):
            deployment.plan(config)

    def test_nonce_proves_host_to_guest_relationship_and_is_removed_on_failure(self):
        def read_guest(path):
            key = 'guest_tools' if '/session-tools/' in path else 'mod'
            return (self.roots[key] / path.rsplit('/', 1)[1]).read_bytes()
        result = qualify(self.config, read_guest)
        self.assertEqual(result['deployment_bindings'], self.config['deployment_bindings'])
        with self.assertRaisesRegex(ValueError, 'does not reach'):
            qualify(self.config, lambda path: b'wrong mapping')
        self.assertTrue(all(not list(root.iterdir()) for root in self.roots.values()))
