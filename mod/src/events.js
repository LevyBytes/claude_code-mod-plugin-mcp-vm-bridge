export function register(on) {
  on('session.start', async ($, e, next) => {
    await refresh($);
    $.clock.every(500, () => tick($));
    return next(e);
  });
  on('turn.start', ($, e, next) => {
    if (!e.agentId) { snapshot.state = 'working'; snapshot.turn_id = e.turnId; }
    emit('turn.start', { turn_id: e.turnId, agent_id: e.agentId });
    return next(e);
  });
  on('turn.complete', ($, e, next) => {
    if (!e.agentId) {
      snapshot.state = e.isAborted && e.turnId !== assistantAbortTurn ? 'interrupted' : 'idle';
      snapshot.turn_id = null;
      assistantAbortTurn = null;
    }
    emit('turn.complete', { turn_id: e.turnId, aborted: e.isAborted, reason: e.reason });
    return next(e);
  });
  on('tool.call', async ($, e, next) => {
    emit('tool.start', { tool: e.tool, agent_id: e.agentId });
    if (!e.agentId) snapshot.state = 'tool_running';
    try { return await next(e); }
    finally {
      emit('tool.end', { tool: e.tool, agent_id: e.agentId });
      if (!e.agentId && snapshot.turn_id) snapshot.state = 'working';
    }
  });
  on('classic.PermissionRequest', ($, e, next) => {
    snapshot.state = 'waiting_owner';
    emit('permission.request', { tool: e.tool_name });
    return next(e);
  });
  on('session.measure', ($, e, next) => {
    snapshot.usage = { context: e.context, rateLimits: e.rateLimits, cost: e.cost };
    return next(e);
  });
  on('turn.step', async function* ($, e, next) {
    const effective = !e.agentId && configured ? { ...e, ...configured } : e;
    if (!e.agentId) {
      snapshot.requested_step = { model: effective.model, effort: effective.effort, turn_id: e.turnId };
      emit('model.request', snapshot.requested_step);
    }
    const stream = next(effective);
    let item = await stream.next();
    while (!item.done) {
      if (item.value.kind === 'text') emit('text', {
        turn_id: e.turnId, text: item.value.text.slice(0, 4000), truncated: item.value.text.length > 4000
      });
      yield item.value;
      item = await stream.next();
    }
    return item.value;
  });
}
