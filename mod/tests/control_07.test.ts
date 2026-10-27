import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('unknown sender cannot submit', async ($, on) => {
  let calls = 0; let polls = 0; let last = null;
  const clock = base(on, body => { last = body; return { ok: true, binding: 'b', commands: polls++ ? [] : [{
    op: 'send', session_id: 'session-a', binding: 'b', request_id: 'r', text: 'hello', source: { kind: 'unknown' }
  }] }; });
  on('prompt.submit', ($, e) => { calls++; return { text: e.text }; });
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  await clock.advance(1000);
  expect(calls).toBe(0);
  expect(last.acks[0].detail).toBe('UNSUPPORTED_SENDER_IDENTITY');
});
