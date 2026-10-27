const test = require('node:test');
const assert = require('node:assert/strict');
const { route, QUALIFIED } = require('./routing');
function fixture() {
  const calls = [], tabs = [];
  class TabInputWebview { constructor(viewType) { this.viewType = viewType; } }
  const vscode = { TabInputWebview, ConfigurationTarget: { Global: 1 },
    window: { tabGroups: { all: [{ tabs }] } },
    workspace: { getConfiguration: () => ({ get: () => 'sidebar',
      update: async (...args) => calls.push(['setting', ...args]) }) },
    commands: { getCommands: async () => ['claude-vscode.editor.open', 'claudeVSCodeSidebarSecondary.focus'],
      executeCommand: async (...args) => { calls.push(args); } } };
  return { vscode, calls, tabs, TabInputWebview };
}
test('new and resume route explicitly to sidebar without a prompt', async () => {
  for (const op of ['new', 'resume']) {
    const { vscode, calls } = fixture();
    const body = { op };
    if (op === 'resume') body.target_session = 'bc6999c7-902f-484b-b53d-f7e095313918';
    const result = await route(vscode, body, QUALIFIED);
    assert.equal(result.sidebar_route_invoked, true);
    assert.deepEqual(calls[2], ['claude-vscode.editor.open', body.target_session,
      undefined, undefined, undefined, undefined, { programmatic: 'honor-preferred-location' }]);
  }
});
test('unknown build, unexpected fields and ambiguous editor tabs never launch', async () => {
  const f = fixture();
  await assert.rejects(route(f.vscode, { op: 'new' }, { ...QUALIFIED, sha256: 'unknown' }), /UNQUALIFIED/);
  await assert.rejects(route(f.vscode, { op: 'new', text: 'prompt' }, QUALIFIED), /Unsupported/);
  await assert.rejects(route(f.vscode, { op: 'resume', target_session: 'not-a-session' }, QUALIFIED), /UUID/);
  f.tabs.push({ input: new f.TabInputWebview('mainThreadWebview-claudeVSCodePanel'), label: 'Owner tab' });
  await assert.rejects(route(f.vscode, { op: 'new' }, QUALIFIED), /CLAUDE_EDITOR_TABS_OPEN/);
  assert.equal(f.calls.length, 0);
});
test('missing sidebar command or unexpected tab after invocation fails explicitly', async () => {
  const f = fixture();
  f.vscode.commands.getCommands = async () => [];
  await assert.rejects(route(f.vscode, { op: 'new' }, QUALIFIED), /unavailable/);
  assert.equal(f.calls.length, 0);
  const g = fixture();
  g.vscode.commands.executeCommand = async command => {
    if (command === 'claude-vscode.editor.open')
      g.tabs.push({ input: new g.TabInputWebview('claudeVSCodePanel'), label: 'Unexpected' });
  };
  await assert.rejects(route(g.vscode, { op: 'new' }, QUALIFIED), /Unexpected editor tab/);
});
