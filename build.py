"""Build from maintained modules; --check rejects stale or edited generated outputs."""
import argparse
import hashlib
import json

from tools.archive import zip_bytes
from tools.files import ROOT, source_files
from tools.vsix import companion
from tools.generated import differences, publish


def outputs():
    maintained = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in source_files()}
    files = {}
    order = ['state', 'wire', 'submission', 'controls', 'transport', 'events']
    files['build/plugin/hooks/register.js'] = b'\n'.join(maintained[f'mod/src/{n}.js'] for n in order)
    for name, data in maintained.items():
        if name.startswith('mod/') and not name.startswith('mod/src/'):
            files['build/plugin/' + name[4:]] = data
        if name.startswith(('claude_session/', 'bridge_runtime/')) or name == 'bridge.py':
            files['build/host/' + name] = data
    for name in ('LICENSE', 'NOTICE'):
        for target in ('build/plugin/', 'build/host/'):
            files[target + name] = maintained[name]
    files['build/claude-sidebar-bridge.vsix'] = companion(maintained)
    manifest = {'schema': 1, 'sources': {n: hashlib.sha256(b).hexdigest() for n, b in maintained.items()},
                'outputs': {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}}
    files['build/manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    archive = {**maintained, **files}
    files['dist/claude-vm-bridge-0.3.0.zip'] = zip_bytes(archive)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = outputs()
    if not args.check:
        publish(ROOT, files)
    stale = differences(ROOT, files)
    print(json.dumps({'mode': 'check' if args.check else 'build', 'outputs': len(files), 'stale': stale}))
    return 1 if stale else 0


if __name__ == '__main__':
    raise SystemExit(main())
