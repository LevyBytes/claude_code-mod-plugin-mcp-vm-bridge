"""Bound Podman transport with explicitly recorded container and mount identity."""
import json
import os
import subprocess

from .paths import INSTALL as INSTALL, ROOT as ROOT, STATE as STATE, atomic as atomic, hidden as hidden
from .binding import inspect_binding


class Backend:
    def __init__(self, config):
        self.config = config
        self.env = {**os.environ, **config.get('environment', {})}
        self.prefix = [config['podman']]
        if config.get('connection'):
            self.prefix += ['--connection', config['connection']]

    def call(self, args, timeout=30):
        result = subprocess.run([*self.prefix, *args], env=self.env, cwd=ROOT,
            stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, **hidden())
        if result.returncode:
            raise RuntimeError('Podman operation failed; inspect the owned instance before retrying')
        return result.stdout.decode('utf-8')

    def verify(self):
        raw = json.loads(self.call(['inspect', self.config['container']]))[0]
        live = inspect_binding(raw)
        if live != self.config['container_binding']:
            raise RuntimeError('Container identity or grants changed; review the instance binding')
        return live
