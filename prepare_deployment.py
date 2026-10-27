"""Populate new dedicated host directories from the checked build; never contact the VM."""
import argparse
from pathlib import Path

from build import outputs
from tools.deployment import GUEST_FILES
from tools.files import ROOT
from tools.generated import differences, unlinked
from bridge_runtime.paths import STATE


def prepare(tools, mod):
    roots = [tools, mod]
    for root in roots:
        if not root.is_absolute():
            raise ValueError('Dedicated absolute deployment directories are required')
        unlinked(root)
        if root.exists() and any(root.iterdir()):
            raise ValueError('Initial deployment directory must be empty: ' + str(root))
        if ROOT.is_relative_to(root.resolve()) or STATE.is_relative_to(root.resolve()):
            raise ValueError('Deployment must not contain source or controller state')
    if tools.is_relative_to(mod) or mod.is_relative_to(tools):
        raise ValueError('Deployment directories must be separate')
    expected = outputs()
    if differences(ROOT, expected):
        raise ValueError('Run build.py before preparing deployment')
    files = [(tools / name, expected['build/host/claude_session/' + name]) for name in GUEST_FILES]
    files += [(mod / name.removeprefix('build/plugin/'), data) for name, data in expected.items()
              if name.startswith('build/plugin/')]
    for path, data in files:
        unlinked(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(data)
    return len(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--guest-tools', required=True, type=Path)
    parser.add_argument('--mod', required=True, type=Path)
    args = parser.parse_args()
    try:
        print('Prepared files:', prepare(args.guest_tools, args.mod))
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
