"""Portable local paths and atomic receipts; never bundled with private instance data."""
import json
import os
import subprocess
from pathlib import Path
from typing import TypedDict
from .workspace import resolve_workspace

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = resolve_workspace(ROOT)
STATE = WORKSPACE / 'runtime'
TOOLS = WORKSPACE / '.tools'
INSTALL = STATE / 'instance.json'


class ProcessOptions(TypedDict, total=False):
    creationflags: int


def hidden() -> ProcessOptions:
    return {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=True, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
