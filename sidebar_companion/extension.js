const vscode = require('vscode');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const net = require('node:net');
const { route } = require('./routing');
let server;

async function activate(context) {
  // One owned workspace/profile only. No host listener, command passthrough or prompt input.
  if (process.platform !== 'linux' || vscode.workspace.workspaceFolders?.length !== 1 ||
      vscode.workspace.workspaceFolders[0].uri.fsPath !== '/workspace') return;
  const directory = path.join(os.homedir(), '.local/state/kaizen-session');
  const socketPath = path.join(directory, 'sidebar.sock');
  const extension = vscode.extensions.getExtension('anthropic.claude-code');
  if (!extension) return;
  await extension.activate();
  const build = { version: extension.packageJSON.version, sha256: crypto.createHash('sha256')
    .update(fs.readFileSync(path.join(extension.extensionPath, 'extension.js'))).digest('hex') };
  if (fs.existsSync(socketPath)) {
    const active = await new Promise(resolve => {
      const probe = net.connect(socketPath);
      probe.once('connect', () => { probe.destroy(); resolve(true); });
      probe.once('error', error => resolve(!['ENOENT', 'ECONNREFUSED'].includes(error.code)));
      probe.setTimeout(1000, () => { probe.destroy(); resolve(true); });
    });
    if (active) return; // Never replace another editor's active socket.
    if (!fs.lstatSync(socketPath).isSocket()) return;
    fs.unlinkSync(socketPath);
  }
  let busy = false;
  server = net.createServer(socket => {
    let buffer = Buffer.alloc(0), handled = false;
    socket.on('error', () => {});
    socket.setTimeout(15000, () => socket.destroy());
    socket.on('data', async chunk => {
      if (handled) return;
      buffer = Buffer.concat([buffer, chunk]);
      if (buffer.length > 8192) { handled = true; socket.destroy(); return; }
      if (!buffer.includes(10)) return;
      handled = true;
      let ownsBusy = false;
      try {
        const body = JSON.parse(buffer.toString('utf8'));
        const token = JSON.parse(fs.readFileSync(path.join(directory, 'relay.json'), 'utf8')).token;
        if (typeof body.token !== 'string' || body.token.length !== token.length ||
            !crypto.timingSafeEqual(Buffer.from(body.token), Buffer.from(token))) throw Error('Unauthorized');
        if (busy) throw Error('Sidebar operation already pending');
        busy = ownsBusy = true;
        const result = await route(vscode, body, build);
        socket.end(JSON.stringify(result) + '\n');
      } catch (error) { socket.end(JSON.stringify({ ok: false, error: error.message }) + '\n'); }
      finally { if (ownsBusy) busy = false; }
    });
  });
  server.on('error', error => console.error('Kaizen sidebar listener: ' + error.code));
  server.listen(socketPath, () => fs.chmodSync(socketPath, 0o600));
  context.subscriptions.push({ dispose: () => server?.close() });
}

function deactivate() { server?.close(); }
module.exports = { activate, deactivate };
