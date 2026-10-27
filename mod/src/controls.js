async function dispatch($, command) {
  if (command.session_id !== sessionId || command.binding !== binding) {
    acknowledge(command, 'rejected', 'Session binding changed');
    return;
  }
  if (!Object.prototype.hasOwnProperty.call(PREFIXES, command.source?.kind)) {
    acknowledge(command, 'rejected', 'UNSUPPORTED_SENDER_IDENTITY'); return;
  }
  if (command.op === 'send') {
    if (pendingSend) { acknowledge(command, 'rejected', 'Another message is pending'); return; }
    // Never wait on prompt submission in the control lane: interrupt must remain available.
    void send($, command);
  } else if (command.op === 'interrupt') {
    try {
      if (command.turn_id !== snapshot.turn_id) throw new Error('Turn changed');
      assistantAbortTurn = command.turn_id;
      await $.turn.abort({ turnId: command.turn_id });
      acknowledge(command, 'interrupt_requested');
    } catch (error) { assistantAbortTurn = null; acknowledge(command, 'rejected', error.message); }
  } else if (command.op === 'configure') {
    if (snapshot.state !== 'idle' || pendingSend) {
      acknowledge(command, 'rejected', 'Session is not idle'); return;
    }
    if (!/^claude-[a-z0-9.-]+(\[1m\])?$/.test(command.model) || command.model.length > 128 ||
        !['low', 'medium', 'high', 'xhigh', 'max'].includes(command.effort)) {
      acknowledge(command, 'rejected', 'Invalid model or effort'); return;
    }
    configured = { model: command.model, effort: command.effort };
    snapshot.configured = configured;
    acknowledge(command, 'completed', 'Session-local request overrides; not yet observed in inference', configured);
  } else if (command.op === 'context') {
    if (contextPending) { acknowledge(command, 'rejected', 'A context report is already running'); return; }
    contextPending = command.request_id;
    // Full counting must not occupy the polling lane needed for interruption.
    void contextReport($, command);
  } else { acknowledge(command, 'rejected', 'Unsupported operation'); }
}

async function contextReport($, command) {
  try {
    if (!['summary', 'full'].includes(command.detail)) throw new Error('Invalid context detail');
    const report = await $.session.usage({ breakdown: command.detail });
    if (await $.session.id() !== command.session_id) throw new Error('Session changed');
    acknowledge(command, 'completed', '', { detail: command.detail, usage: report });
  } catch (error) { acknowledge(command, 'rejected', error.message); }
  finally { if (contextPending === command.request_id) contextPending = null; }
}
