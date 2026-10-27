"""Freeze validated payload bytes and exact destinations before running update checks."""
import hashlib
import json
import os
from datetime import datetime, timezone

from build import outputs
from .files import ROOT
from .generated import differences, unlinked
from .deployment_ownership import DeploymentPlan, reconcile, save
from .grants import grants
from bridge_runtime.paths import STATE

GUEST_FILES = ['__init__.py', 'identity.py', 'protocol.py', 'state.py', 'state_tick.py', 'session_registry.py',
               'tick_validation.py', 'request_ledger.py', 'state_client.py', 'state_submit.py',
               'relay.py', 'guest_client.py', 'guest_desktop.py']


def plan(config):
    roots, _ = grants(config)
    expected = outputs()
    if differences(ROOT, expected):
        raise ValueError('Generated outputs differ from source; run build.py before update')
    payloads = {key: {} for key in roots}
    for name in GUEST_FILES:
        payloads['guest_tools'][name] = expected['build/host/claude_session/' + name]
    for name, data in expected.items():
        if name.startswith('build/plugin/'):
            payloads['mod'][name.removeprefix('build/plugin/')] = data
    rows = DeploymentPlan()
    for key, target_root in roots.items():
        entries, record = reconcile(STATE, target_root, payloads[key])
        for _, target in entries:
            unlinked(target)
        rows.extend(entries)
        rows.ownership.append(record)
    return rows


def apply(rows):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = STATE / 'updates' / stamp
    backup.mkdir(parents=True)
    records = []
    for index, (data, target) in enumerate(rows):
        unlinked(target)
        old = target.read_bytes() if target.exists() else None
        if old is not None:
            (backup / str(index)).write_bytes(old)
        records.append({'target': str(target), 'backup': str(index) if old is not None else None,
                        'sha256': hashlib.sha256(data).hexdigest() if data is not None else None})
    (backup / 'manifest.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    for data, target in rows:
        unlinked(target)
        if data is None:
            target.unlink(missing_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.bridge-update.tmp')
        unlinked(temporary)
        temporary.write_bytes(data)
        os.replace(temporary, target)
    save(rows)
    return str(backup)
