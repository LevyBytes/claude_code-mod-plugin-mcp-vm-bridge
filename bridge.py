"""Standalone host CLI or MCP server. Local state stays in the external workspace."""
import os
import sys
import tempfile
from bridge_runtime.paths import STATE
from claude_session.cli import main

if __name__ == '__main__':
    sys.dont_write_bytecode = True
    scratch = STATE / 'tmp'
    scratch.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(scratch)
    os.environ['TMP'] = os.environ['TEMP'] = str(scratch)
    raise SystemExit(main())
