import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('stream remains unchanged and text observation is bounded', async ($, on) => {
  let last = null;
  const clock = base(on, body => { last = body; return { ok: true, binding: 'b', commands: [] }; });
  on('turn.step', async function* ($, e) {
    yield { kind: 'text', index: 0, text: 'x'.repeat(6000) };
    return { turnId: e.turnId, index: e.index, answer: 'done', toolUses: [], stopReason: 'end_turn', usage: null };
  });
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  const stream = $.turn.step({ turnId: 't', index: 0, model: 'test', messageCount: 1 });
  expect((await stream.next()).value.text.length).toBe(6000);
  expect((await stream.next()).value.answer).toBe('done');
  await clock.advance(500);
  const text = last.events.find(row => row.kind === 'text');
  expect(text.text.length).toBe(4000);
  expect(text.truncated).toBe(true);
});

for (const kind of ['llama.cpp', 'ollama', 'vllm']) {
  test(kind + ' receives OAR prefix', async ($, on) => {
    let submitted = null; let polls = 0;
    const clock = base(on, body => ({ ok: true, binding: 'b', commands: polls++ ? [] : [{
      op: 'send', session_id: 'session-a', binding: 'b', request_id: 'r', text: 'hello',
      source: { kind, method: 'runtime_adapter' }
    }] }));
    on('prompt.submit', ($, e) => { submitted = e; return { text: e.text }; });
    await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
    await clock.advance(1000);
    expect(submitted.text).toBe('OAR: hello');
  });
}
