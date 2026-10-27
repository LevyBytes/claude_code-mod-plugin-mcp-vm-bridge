"""Render one MCP entry, preserving unrelated TOML values and external workspace routing."""
import json
import re
import tomllib


def render(before, root, executable, workspace):
    data = tomllib.loads(before)
    entry = 'mcp_servers.kaizen_claude_vm'
    q = json.dumps
    stanza = (f'[{entry}]\ncommand = {q(str(executable))}\n'
              f'args = {q(["-B", "-X", "utf8", str(root / "bridge.py"), "mcp"])}\n'
              f'cwd = {q(str(root))}\nstartup_timeout_sec = 20\ntool_timeout_sec = 90\n'
              f'env = {{ CLAUDE_VM_BRIDGE_WORKSPACE = {q(str(workspace))} }}\n')
    lines = before.splitlines(keepends=True)
    headers = [(i, line.strip()) for i, line in enumerate(lines) if re.match(r'^\s*\[', line)]
    removals = []
    for offset, (start, header) in enumerate(headers):
        if re.fullmatch(r'\[' + re.escape(entry) + r'(?:\.[A-Za-z0-9_-]+)*\]\s*(?:#.*)?', header):
            end = headers[offset + 1][0] if offset + 1 < len(headers) else len(lines)
            removals.append((start, end))
    existing = 'kaizen_claude_vm' in data.get('mcp_servers', {})
    if existing and not removals:
        raise ValueError('Unsupported MCP table spelling; use ordinary unquoted table headers')
    for start, end in reversed(removals):
        del lines[start:end]
    text = ''.join(lines).rstrip() + '\n\n' + stanza
    changed = tomllib.loads(text)
    changed['mcp_servers'].pop('kaizen_claude_vm')
    if existing:
        data['mcp_servers'].pop('kaizen_claude_vm')
    if not changed.get('mcp_servers'):
        changed.pop('mcp_servers', None)
    if not data.get('mcp_servers'):
        data.pop('mcp_servers', None)
    if changed != data:
        raise ValueError('Unrelated configuration would change; refusing registration')
    return text
