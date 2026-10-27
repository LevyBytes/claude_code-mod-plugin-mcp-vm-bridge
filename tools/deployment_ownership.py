"""Track publisher-owned files outside mappings; never delete unrecognized destination files."""
import hashlib
import json
from .generated import inventory
from bridge_runtime.paths import atomic


class DeploymentPlan(list):
    def __init__(self):
        super().__init__()
        self.ownership = []


def record_path(state, root):
    digest = hashlib.sha256(str(root).encode()).hexdigest()
    return state / 'deployments' / (digest + '.json')


def reconcile(state, root, payload):
    record = record_path(state, root)
    previous = set()
    if record.exists():
        data = json.loads(record.read_text(encoding='utf-8'))
        if data.get('root') != str(root) or not isinstance(data.get('files'), list):
            raise ValueError('Invalid deployment ownership record')
        previous = set(data['files'])
    for name in previous:
        target = root / name
        if not target.resolve().is_relative_to(root) or target == root:
            raise ValueError('Invalid managed deployment path')
    actual = inventory(root, ('.',))
    unknown = actual.keys() - payload.keys() - previous
    if unknown:
        raise ValueError('Unmanaged deployment files; preserve them or choose new empty roots: ' +
                         ', '.join(sorted(unknown)[:5]))
    names = payload.keys() | previous
    rows = [(payload.get(name), root / name) for name in sorted(names)]
    return rows, (record, {'root': str(root), 'files': sorted(payload)})


def save(plan):
    for path, data in plan.ownership:
        atomic(path, data)
