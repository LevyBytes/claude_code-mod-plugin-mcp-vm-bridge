"""Qualify each host directory through its guest read-only mapping before recording it."""
import json
import secrets
import subprocess

from bridge_runtime.backend import Backend, hidden, atomic
from bridge_runtime.binding import inspect_binding
from bridge_runtime.paths import INSTALL
from .grants import grants


def inspect(config):
    backend = Backend(config)
    raw = json.loads(backend.call(['inspect', config['container']]))[0]
    return {**config, 'container_binding': inspect_binding(raw)}


def qualify(config, read_guest=None):
    roots, bindings = grants(config, require_binding=False)
    backend = Backend(config)
    for key, root in roots.items():
        name = '.bridge-map-proof-' + secrets.token_hex(16)
        path = root / name
        proof = secrets.token_bytes(32)
        guest = bindings[key]['guest_destination'] + '/' + name
        created = False
        try:
            with path.open('xb') as handle:
                created = True
                handle.write(proof)
            if read_guest is not None:
                observed = read_guest(guest)
            else:
                code = 'import pathlib,sys;sys.stdout.buffer.write(pathlib.Path(sys.argv[1]).read_bytes())'
                result = subprocess.run([*backend.prefix, 'exec', '-i', '--user', '1000:1000',
                    config['container_binding']['id'], 'python3', '-B', '-', guest],
                    input=code.encode(), capture_output=True, timeout=15, env=backend.env, **hidden())
                if result.returncode:
                    raise ValueError('Guest could not read mapping proof: ' + key)
                observed = result.stdout
            if observed != proof:
                raise ValueError('Host directory does not reach the selected guest mount: ' + key)
        finally:
            if created:
                path.unlink(missing_ok=True)
    backend.verify() if read_guest is None else None
    return {**config, 'deployment_bindings': bindings}


def save(config, path=INSTALL):
    if path.exists():
        previous = json.loads(path.read_text(encoding='utf-8'))
        atomic(path.with_name('instance.before-' + secrets.token_hex(8) + '.json'), previous)
    atomic(path, config)
