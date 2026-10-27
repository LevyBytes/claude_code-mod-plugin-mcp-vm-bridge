"""Exact generated inventories; never follow links while checking or replacing owned output."""
import os
from pathlib import Path


def unlinked(path):
    for candidate in [path, *path.parents]:
        if candidate.is_symlink() or candidate.is_junction():
            raise ValueError('Linked generated/deployment path: ' + str(candidate))


def inventory(root, names=('build', 'dist')):
    found = {}
    for name in names:
        folder = root / name
        unlinked(folder)
        if not folder.exists():
            continue
        for directory, children, files in os.walk(folder, followlinks=False):
            base = Path(directory)
            for entry in [*children, *files]:
                unlinked(base / entry)
            for entry in files:
                path = base / entry
                found[path.relative_to(root).as_posix()] = path
    return found


def differences(root, expected):
    actual = inventory(root)
    return sorted(set(actual) - expected.keys() | {
        name for name, data in expected.items() if name not in actual or actual[name].read_bytes() != data})


def publish(root, expected):
    root = root.resolve(strict=True)
    actual = inventory(root)
    for name, data in expected.items():
        path = root / name
        if not path.resolve().is_relative_to(root) or Path(name).parts[0] not in {'build', 'dist'}:
            raise ValueError('Output outside generated roots')
        unlinked(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.build.tmp')
        unlinked(temporary)
        temporary.write_bytes(data)
        os.replace(temporary, path)
    for name in sorted(set(actual) - expected.keys()):
        path = actual[name]
        unlinked(path)
        if not path.resolve().is_relative_to(root):
            raise ValueError('Unexpected stale output location')
        path.unlink()
