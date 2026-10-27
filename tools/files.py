"""Enumerate public source only; local/AI state is a layout error, never release input."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', 'build', 'dist', '__pycache__', '.ruff_cache'}
PUBLIC_DIRS = {'bridge_runtime', 'claude_session', 'mod', 'sidebar_companion', 'tests', 'tools', 'docs'}
PUBLIC_FILES = {'.editorconfig', '.gitattributes', '.gitignore', 'LICENSE', 'NOTICE', 'README.md',
                'pyproject.toml', 'pyrightconfig.json', 'requirements-dev.txt', 'CHANGELOG.md', 'CONTRIBUTING.md'}
LOCAL = {'AGENTS.md', 'CLAUDE.md', 'STATUS.md', 'GIT_SETUP.md', 'provenance.json',
         'runtime', '.tools', '.agents', '.codex', '.claude'}
LOCAL_FOLDED = {name.casefold() for name in LOCAL}
CODE = {'.py', '.js', '.mjs', '.ts', '.ps1', '.sh'}


def source_files(root=ROOT):
    for directory, children, names in os.walk(root, followlinks=False):
        base = Path(directory)
        entries = [*children, *names]
        for name in entries:
            if name.casefold() in LOCAL_FOLDED:
                raise ValueError('Local/AI material belongs in the external workspace: ' + str(base / name))
            if base == root and name not in SKIP | PUBLIC_DIRS | PUBLIC_FILES and not name.endswith('.py'):
                raise ValueError('Undeclared public source entry: ' + str(base / name))
        children[:] = sorted(n for n in children if n not in SKIP)
        for child in list(children):
            path = base / child
            if path.is_symlink() or path.is_junction():
                raise ValueError('Linked source directory: ' + str(path))
        for name in sorted(names):
            if name in SKIP:
                continue
            path = base / name
            if path.is_symlink():
                raise ValueError('Linked source file: ' + str(path))
            yield path
