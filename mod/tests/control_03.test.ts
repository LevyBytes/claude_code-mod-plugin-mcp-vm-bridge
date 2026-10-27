import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('wrong session command never submits', async ($, on) => {
  let calls = 0;
  let polls = 0;
  let last = null;
  const clock = base(on, body => {
    last = body;
    return { ok: true, binding: 'binding-a', commands: polls++ ? [] : [{
      op: 'send', session_id: 'different-session', binding: 'binding-a', request_id: 'r1', text: 'Wrong'
    }] };
  });
  on('prompt.submit', ($, e) => { calls++; return { text: e.text }; });
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  await clock.advance(1000);
  expect(calls).toBe(0);
});
