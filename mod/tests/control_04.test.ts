import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('owner interruption stays interrupted; status does not invent token counts', async ($, on) => {
  let last = null;
  const clock = base(on, body => { last = body; return { ok: true, binding: 'b', commands: [] }; });
  on('turn.complete', () => ({ text: '' }));
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  await $.turn.complete({ turnId: 't', answer: '', durationMs: 1, isAborted: true, usage: null });
  await clock.advance(500);
  expect(last.snapshot.state).toBe('interrupted');
  expect(last.snapshot.usage.context.tokens).toBeUndefined();
});
