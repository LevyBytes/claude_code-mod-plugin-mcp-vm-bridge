function utf8Size(text) {
  let size = 0;
  for (const character of text) {
    const point = character.codePointAt(0);
    size += point < 128 ? 1 : point < 2048 ? 2 : point < 65536 ? 3 : 4;
  }
  return size;
}

function observation() {
  if (dropped && events.length < 256) { emit('gap', { dropped }); dropped = 0; }
  const body = { session_id: sessionId, instance_id: instanceId, snapshot, batch: ++batchNumber,
    events: events.slice(0, 16), acks: acknowledgements.slice(0, 1) };
  let text = JSON.stringify(body);
  while (utf8Size(text) > 240000 && body.events.length) {
    body.events.pop();
    text = JSON.stringify(body);
  }
  if (utf8Size(text) > 240000) throw Error('Observation exceeds transport limit');
  events.splice(0, body.events.length);
  acknowledgements.splice(0, body.acks.length);
  return { text, batch: body.batch, session: sessionId };
}
