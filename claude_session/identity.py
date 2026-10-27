"""Automatic operational attribution; never an owner-approval or hostile-process boundary."""
import base64
import json
import os
import subprocess
from pathlib import Path

PREFIXES = {'codex': 'CODEX: ', 'llama.cpp': 'OAR: ', 'ollama': 'OAR: ', 'vllm': 'OAR: '}
CONTROL_OPS = frozenset({'send', 'interrupt', 'configure', 'context', 'open'})
UNSUPPORTED = ('UNSUPPORTED_SENDER_IDENTITY: this sending client is not yet supported. '
               'Add or update a tested integration adapter; no message or control was submitted.')


def ancestry():
    """Read executable ancestry only. Never return process arguments or environment secrets."""
    if os.name == 'nt':
        script = ('$p=' + str(os.getpid()) + '; $rows=@(); $seen=@{}; '
                  'for($i=0;$i -lt 16 -and $p -gt 0 -and -not $seen.ContainsKey($p);$i++) {'
                  '$seen[$p]=$true; $r=Get-CimInstance Win32_Process -Filter "ProcessId=$p"; '
                  'if(-not $r){break}; $rows+=@{name=$r.Name;path=$r.ExecutablePath}; '
                  '$p=[int]$r.ParentProcessId }; ConvertTo-Json -Compress -InputObject @($rows)')
        executable = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        result = subprocess.run([str(executable), '-NoProfile', '-NonInteractive', '-EncodedCommand',
                                 base64.b64encode(script.encode('utf-16le')).decode()],
                                capture_output=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise ValueError(UNSUPPORTED)
        return json.loads(result.stdout.decode('utf-8-sig'))
    rows, pid, seen = [], os.getpid(), set()
    while pid > 0 and pid not in seen and len(rows) < 16:
        seen.add(pid)
        proc = Path('/proc') / str(pid)
        try:
            executable = proc.joinpath('exe').resolve(strict=True)
            rows.append({'name': executable.name, 'path': str(executable)})
            status = proc.joinpath('status').read_text()
            pid = int(next(line.split()[1] for line in status.splitlines() if line.startswith('PPid:')))
        except (OSError, ValueError, StopIteration):
            break
    return rows


def classify(rows):
    # Prefer the nearest recognized integration, not an inherited environment variable.
    names = {'codex': 'codex', 'codex.exe': 'codex', 'llama-server': 'llama.cpp',
             'llama-server.exe': 'llama.cpp', 'ollama': 'ollama', 'ollama.exe': 'ollama',
             'vllm': 'vllm', 'vllm.exe': 'vllm'}
    for row in rows:
        name = str(row.get('name', '')).lower()
        path = str(row.get('path') or '').replace('\\', '/')
        if name in names and path and path.rsplit('/', 1)[-1].lower() == name:
            return {'kind': names[name], 'method': 'executable_ancestry'}
    raise ValueError(UNSUPPORTED)


def detect():
    try:
        return classify(ancestry())
    except (OSError, KeyError, subprocess.TimeoutExpired):
        raise ValueError(UNSUPPORTED) from None


def validate(source):
    if (not isinstance(source, dict) or set(source) != {'kind', 'method'}
            or source['kind'] not in PREFIXES
            or source['method'] not in {'executable_ancestry', 'runtime_adapter'}):
        raise ValueError(UNSUPPORTED)
    return dict(source)
