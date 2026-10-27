import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('Codex request reaches same session with CODEX and plugin origin', async ($, on) => {
  let submitted = null;
  let polls = 0;
  let last = null;
  const clock = base(on, body => {
    last = body;
    return { ok: true, binding: 'binding-a', commands: polls++ ? [] : [{
      op: 'send', session_id: 'session-a', binding: 'binding-a', request_id: 'r1', text: 'Inspect only',
      source: { kind: 'codex', method: 'executable_ancestry' }
    }] };
  });
  on('prompt.submit', ($, e) => { submitted = e; return { text: e.text }; });
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  await clock.advance(1000);
  expect(submitted.text).toBe('CODEX: Inspect only');
  expect(submitted.origin).toMatchObject({ kind: 'plugin', name: 'kaizen-session' });
  expect(last.acks[0].state).toBe('started');
});
