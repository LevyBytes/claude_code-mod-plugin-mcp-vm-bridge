"""Inspect and bind an existing Podman desktop; --apply proves mappings and records local state."""
import argparse
import json
from pathlib import Path

from bridge_runtime.paths import INSTALL
from tools.bind_instance import inspect, qualify, save
from tools.grants import grants


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--podman', required=True, type=Path, help='Absolute Podman executable path')
    parser.add_argument('--container', required=True, help='Existing running desktop container name or ID')
    parser.add_argument('--connection', help='Optional Podman connection name')
    parser.add_argument('--guest-tools', required=True, type=Path, help='Dedicated absolute host tool directory')
    parser.add_argument('--mod', required=True, type=Path, help='Dedicated absolute host plugin directory')
    parser.add_argument('--environment-file', type=Path, help='External JSON object of Podman environment values')
    parser.add_argument('--apply', action='store_true', help='Prove mappings and save the external instance binding')
    args = parser.parse_args()
    if not args.podman.is_absolute() or not args.podman.is_file():
        parser.error('--podman must name an existing absolute executable path')
    environment = json.loads(args.environment_file.read_text(encoding='utf-8')) if args.environment_file else {}
    if not isinstance(environment, dict) or not all(isinstance(v, str) for v in environment.values()):
        parser.error('--environment-file must contain a JSON object of string values')
    config = inspect({'podman': str(args.podman), 'container': args.container, 'connection': args.connection,
                      'environment': environment,
                      'deployment': {'guest_tools': str(args.guest_tools), 'mod': str(args.mod)}})
    _, bindings = grants(config, require_binding=False)
    if args.apply:
        config = qualify(config)
        save(config)
    print(json.dumps({'applied': args.apply, 'instance_file': str(INSTALL), 'deployment_bindings': bindings,
                      'mapping_proofs_passed': args.apply}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
