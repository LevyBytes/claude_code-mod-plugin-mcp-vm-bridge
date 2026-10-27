"""Guest-only offline plugin tests with isolated config and no inference."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

scratch = Path(tempfile.mkdtemp(prefix='bridge-check-', dir=str(Path.home() / '.local/state/kaizen-session')))
plugin = scratch / 'plugin'
with zipfile.ZipFile(sys.argv[1]) as archive:
    for entry in archive.infolist():
        relative = PurePosixPath(entry.filename)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid bundle path')
        target = plugin.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(entry))
config = scratch / 'config'
config.mkdir(mode=0o700)
environment = os.environ.copy()
environment['CLAUDE_CONFIG_DIR'] = str(config)
environment['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'] = '1'
for key in ('CLAUDE_CODE_PLUGIN_DIRS', 'CLAUDE_CODE_PROJECT_DIR_NAME'):
    environment.pop(key, None)
matches = list(Path('/home/kaizen/editor-state/extensions').glob('anthropic.claude-code-*-linux-x64'))
assert len(matches) == 1
binary = matches[0] / 'resources/native-binary/claude'
results = []
for args in (['plugin', 'validate', str(plugin)], ['plugin', 'test', str(plugin)]):
    result = subprocess.run([str(binary), *args], cwd=scratch, env=environment,
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    results.append({'args': args, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    if result.returncode:
        break
print(json.dumps({'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'results': results,
    'passed': all(r['exit_code'] == 0 for r in results), 'model_prompts_sent': 0}))
