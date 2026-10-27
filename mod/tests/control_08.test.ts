import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('configuration applies only to main requests without changing stored settings', async ($, on) => {
  let polls = 0; let observed = null;
  const clock = base(on, body => ({ ok: true, binding: 'b', commands: polls++ ? [] : [{
    op: 'configure', session_id: 'session-a', binding: 'b', request_id: 'r',
    model: 'claude-opus-5-5', effort: 'xhigh', source: { kind: 'codex' }
  }] }));
  on('turn.step', async function* ($, e) {
    observed = e;
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null };
  });
  await $.session.start({ surface: 'vscode', isInteractive: true, cwd: '/workspace' });
  await clock.advance(500);
  await $.turn.step({ turnId: 't', index: 0, model: 'other', messageCount: 1 }).next();
  expect(observed.model).toBe('claude-opus-5-5');
  expect(observed.effort).toBe('xhigh');
});
