"""Bind absolute host deployment roots to the explicitly qualified Podman mount sources."""
from pathlib import Path
from .generated import unlinked
from .files import ROOT
from bridge_runtime.paths import STATE

DESTINATIONS = {'guest_tools': '/opt/kaizen/session-tools', 'mod': '/opt/kaizen/claude-session-mod'}


def canonical(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError('Deployment roots must be absolute')
    unlinked(path)
    path = path.resolve(strict=True)
    if not path.is_dir() or path.parent == path:
        raise ValueError('A dedicated deployment directory is required')
    return path


def grants(config, require_binding=True):
    roots = {key: canonical(config['deployment'][key]) for key in DESTINATIONS}
    if roots['mod'].is_relative_to(roots['guest_tools']) or roots['guest_tools'].is_relative_to(roots['mod']):
        raise ValueError('Deployment roots must be separate directories')
    if any(ROOT.is_relative_to(path) or STATE.is_relative_to(path) for path in roots.values()):
        raise ValueError('Deployment must not contain the source checkout or controller state')
    matches = {}
    for key, destination in DESTINATIONS.items():
        mounts = [m for m in config['container_binding']['mounts'] if m['Destination'] == destination]
        if len(mounts) != 1 or mounts[0]['Type'] != 'bind' or mounts[0]['RW'] is not False:
            raise ValueError('Missing unique read-only bind mount: ' + destination)
        matches[key] = {'host_path': str(roots[key]), 'vm_source': mounts[0]['Source'],
                        'guest_destination': destination}
    if require_binding and config.get('deployment_bindings') != matches:
        raise ValueError('Deployment roots do not match qualified mounts; run configure_instance.py --apply')
    return roots, matches
