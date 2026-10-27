const CONFIG = '/home/kaizen/.local/state/kaizen-session/relay.json';
let transport = null;
let sessionId = '';
let instanceId = '';
let binding = '';
let snapshot = { state: 'unknown', turn_id: null };
let events = [];
let acknowledgements = [];
let polling = false;
let inFlight = null;
let batchNumber = 0;
let pendingSend = false;
let assistantAbortTurn = null;
let dropped = 0;
let configured = null;
let contextPending = null;
const PREFIXES = { codex: 'CODEX: ', 'llama.cpp': 'OAR: ', ollama: 'OAR: ', vllm: 'OAR: ' };

function emit(kind, data = {}) {
  if (events.length >= 256) { dropped++; return; }
  events.push({ kind, ...data });
}

function acknowledge(command, state, detail = '', result) {
  if (command.session_id !== sessionId) return;
  const ack = { request_id: command.request_id, state, detail: String(detail).slice(0, 1000) };
  if (result !== undefined) ack.result = result;
  if (utf8Size(JSON.stringify(ack)) > 90000) {
    ack.state = 'rejected'; ack.detail = 'Result exceeds bridge limit'; delete ack.result;
  }
  acknowledgements.push(ack);
}

async function refresh($) {
  const id = await $.session.id();
  if (id !== sessionId) {
    sessionId = id;
    instanceId = String(await $.clock.now()) + '-' + Math.random().toString(36).slice(2);
    binding = '';
    inFlight = null;
    batchNumber = 0;
    events = [];
    acknowledgements = [];
    snapshot = { state: 'idle', turn_id: null };
    pendingSend = false;
    assistantAbortTurn = null;
    configured = null;
    contextPending = null;
  }
  snapshot = { ...snapshot, cwd: await $.session.cwd(), root: await $.session.root(),
    model: await $.session.model(), version: await $.session.version(),
    surfaces: await $.session.surfaces(), usage: await $.session.usage(), configured,
    capabilities: ['send', 'interrupt', 'configure', 'context.summary', 'context.full'],
    protocol: 3 };
}
