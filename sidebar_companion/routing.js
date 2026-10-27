// This argument contract was inspected in the exact installed build below.
// Unknown builds require qualification; matching version text alone is insufficient.
const QUALIFIED = {
  version: '2.1.310',
  sha256: 'b53c3297d5ab0d0403a875ec906120c978e886e2d97578e706f4e2677b8aa781'
};
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

function validate(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body) ||
      Object.keys(body).some(k => !['op', 'target_session', 'token'].includes(k)) ||
      !['status', 'new', 'resume'].includes(body.op)) throw Error('Unsupported sidebar request');
  if (body.op === 'resume' ? !UUID.test(body.target_session ?? '') : 'target_session' in body)
    throw Error('Resume requires one canonical session UUID; other operations accept none');
}

function claudeTabs(vscode) {
  return vscode.window.tabGroups.all.flatMap(group => group.tabs).filter(tab =>
    tab.input instanceof vscode.TabInputWebview && /claudeVSCodePanel/.test(tab.input.viewType));
}

async function route(vscode, body, build) {
  validate(body);
  const tabs = claudeTabs(vscode);
  const qualified = build.version === QUALIFIED.version && build.sha256 === QUALIFIED.sha256;
  if (body.op === 'status') return { ok: true, qualified, build, claude_editor_tabs: tabs.map(t => t.label),
    preferred_location: vscode.workspace.getConfiguration('claudeCode').get('preferredLocation') };
  if (!qualified) throw Error('UNQUALIFIED_CLAUDE_BUILD: qualify the sidebar adapter for this build');
  if (tabs.length) throw Error('CLAUDE_EDITOR_TABS_OPEN: close Claude editor tabs before sidebar lifecycle control');
  const commands = await vscode.commands.getCommands(true);
  if (!['claude-vscode.editor.open', 'claudeVSCodeSidebarSecondary.focus'].every(c => commands.includes(c)))
    throw Error('Required sidebar commands unavailable');
  await vscode.workspace.getConfiguration('claudeCode').update(
    'preferredLocation', 'sidebar', vscode.ConfigurationTarget.Global);
  await vscode.commands.executeCommand('claudeVSCodeSidebarSecondary.focus');
  await vscode.commands.executeCommand('claude-vscode.editor.open', body.target_session,
    undefined, undefined, undefined, undefined, { programmatic: 'honor-preferred-location' });
  if (claudeTabs(vscode).length) throw Error('Unexpected editor tab after sidebar command; inspect before retry');
  return { ok: true, sidebar_route_invoked: true, model_prompts_sent: 0 };
}

module.exports = { QUALIFIED, validate, claudeTabs, route };
