import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('context returns structured usage without submitting a slash command', async ($, on) => {
  let polls = 0; let last = null;
  const clock = base(on, body => { last = body; return { ok: true, binding: 'b', commands: polls++ ? [] : [{
    op: 'context', session_id: 'session-a', binding: 'b', request_id: 'r', detail: 'summary',
    source: { kind: 'codex' }
  }] }; });
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  await clock.advance(1000);
  expect(last.acks[0].state).toBe('completed');
  expect(last.acks[0].result.detail).toBe('summary');
});
