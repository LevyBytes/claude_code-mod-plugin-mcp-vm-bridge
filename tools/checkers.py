"""Real checker subprocesses; absence is a failure rather than a silent skip."""
import os
import shutil
import subprocess
import sys

from .files import ROOT
from bridge_runtime.paths import STATE, TOOLS


def commands():
    node = shutil.which('node')
    pyright = shutil.which('pyright.cmd') if os.name == 'nt' else shutil.which('pyright')
    if not node or not pyright:
        raise RuntimeError('Node and Pyright must be installed and resolvable; no PATH changes are made here')
    # Resolve the npm wrapper to its actual JS entry; avoid cmd-shell quoting and .ps1 policies.
    if os.name == 'nt':
        from pathlib import Path
        entry = Path(pyright).parent / 'node_modules/pyright/index.js'
        pyright_command = [node, str(entry)]
    else:
        pyright_command = [pyright]
    python = [sys.executable, '-B', '-X', 'utf8']
    return [
        ('ruff', [*python, '-m', 'ruff', 'check', '--no-cache', '.']),
        ('pyright', [*pyright_command, '--project', str(ROOT / 'pyrightconfig.json')]),
        ('python_tests', [*python, '-m', 'unittest', 'discover', '-s', 'tests', '-t', '.']),
        ('sidebar_tests', [node, '--test', 'sidebar_companion/routing.test.js']),
        ('mod_transport_tests', [node, '--test', 'tests/mod_transport.test.js']),
        ('sidebar_syntax', [node, '--check', 'sidebar_companion/extension.js']),
        ('mod_syntax', [node, '--input-type=module', '--check']),
        ('build_freshness', [*python, 'build.py', '--check']),
    ]


def run_checks():
    env = dict(os.environ)
    env['PYTHONPATH'] = str(TOOLS / 'python')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['TEMP'] = env['TMP'] = str(STATE / 'tmp')
    (STATE / 'tmp').mkdir(parents=True, exist_ok=True)
    rows = []
    for name, argv in commands():
        data = (ROOT / 'build/plugin/hooks/register.js').read_text() if name == 'mod_syntax' else None
        result = subprocess.run(argv, input=data, capture_output=True, text=True, encoding='utf-8',
                                cwd=ROOT, env=env, timeout=120)
        rows.append({'check': name, 'passed': result.returncode == 0, 'exit_code': result.returncode,
                     'stdout': result.stdout, 'stderr': result.stderr})
        print(f'{name}: {"PASS" if result.returncode == 0 else "FAIL"}', flush=True)
    return rows
