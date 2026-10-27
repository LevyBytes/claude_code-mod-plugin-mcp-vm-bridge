import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('interrupt targets the recorded live turn', async ($, on) => {
  let aborted = null;
  let polls = 0;
  const clock = base(on, body => ({ ok: true, binding: 'b', commands: polls++ ? [] : [{
    op: 'interrupt', session_id: 'session-a', binding: 'b', request_id: 'r', turn_id: 't',
    source: { kind: 'codex', method: 'executable_ancestry' }
  }] }));
  on('turn.start', ($, e) => ({ turnId: e.turnId }));
  on('turn.abort', ($, e) => { aborted = e.turnId; return { value: undefined }; });
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  await $.turn.start({ turnId: 't' });
  await clock.advance(500);
  expect(aborted).toBe('t');
});
