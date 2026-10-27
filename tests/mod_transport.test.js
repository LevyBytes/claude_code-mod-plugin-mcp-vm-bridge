const test = require('node:test');
const assert = require('node:assert/strict');
const {fixture, reply} = require('./mod_fixture');

test('lost acknowledgement response retries identical data and never repeats the prompt', async () => {
  const attempts = [];
  let failed = false;
  const command = {op: 'send', session_id: 'session-a', binding: 'binding-a',
    request_id: 'r1', text: 'Synthetic only', source: {kind: 'codex'}};
  const f = fixture(body => {
    attempts.push(body);
    if (body.batch === 1) return reply(body, [command]);
    if (!failed) { failed = true; throw Error('Synthetic lost response'); }
    return reply(body);
  });
  await f.tick();
  await new Promise(resolve => setImmediate(resolve));
  f.context.emit('turn.complete', {turn_id: 't1'});
  await f.tick();
  await f.tick();
  assert.equal(f.calls.length, 1);
  assert.equal(f.calls[0].text, 'CODEX: Synthetic only');
  assert.deepEqual(attempts[1], attempts[2]);
  assert.equal(attempts[2].acks[0].state, 'started');
  assert.equal(attempts[2].events[0].kind, 'turn.complete');
  assert.equal(f.value('inFlight'), null);
});

test('malformed and non-OK responses preserve pending data', async () => {
  let failure = 0;
  const attempts = [];
  const f = fixture(body => {
    attempts.push(body);
    if (failure++ === 0) return {ok: false, text: '{invalid'};
    if (failure === 2) return {ok: false, text: '{"ok":false}'};
    return reply(body);
  });
  await f.context.refresh(f.$);
  f.context.emit('text', {text: ' retained '});
  await f.tick(); await f.tick(); await f.tick();
  assert.deepEqual(attempts[0], attempts[1]);
  assert.deepEqual(attempts[1], attempts[2]);
  assert.equal(attempts[2].events[0].text, ' retained ');
});

test('UTF-8 wire batches stay bounded and retain events deferred to the next batch', async () => {
  const attempts = [];
  const f = fixture(body => { attempts.push(body); return reply(body); });
  await f.context.refresh(f.$);
  for (let i = 0; i < 16; i++) f.context.emit('text', {text: '漢'.repeat(4000)});
  f.context.acknowledge({session_id: 'session-a', request_id: 'r'}, 'completed', '', 'z'.repeat(89000));
  await f.tick(); await f.tick();
  assert(attempts.every(body => Buffer.byteLength(JSON.stringify(body)) <= 240000));
  assert.equal(attempts.reduce((sum, body) => sum + body.events.length, 0), 16);
});
