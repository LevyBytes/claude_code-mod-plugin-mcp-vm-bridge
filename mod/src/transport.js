async function tick($) {
  if (polling) return;
  polling = true;
  try {
    if (!transport) {
      transport = JSON.parse(await $.fs.read(CONFIG));
      if (transport.url !== 'http://127.0.0.1:39086' || typeof transport.token !== 'string') {
        throw new Error('Unexpected relay configuration');
      }
    }
    await refresh($);
    // Retry the identical observation until confirmed. This does not submit another model prompt.
    if (!inFlight) inFlight = observation();
    const response = await $.http.fetch(transport.url + '/mod', {
      method: 'POST', headers: { Authorization: 'Bearer ' + transport.token, 'Content-Type': 'application/json' },
      body: inFlight.text
    });
    const reply = JSON.parse(response.text);
    if (!response.ok || !reply.ok || reply.batch !== inFlight.batch ||
        typeof reply.binding !== 'string' || !Array.isArray(reply.commands)) {
      transport = null;
      return;
    }
    // Commit delivery before dispatch: a local dispatch error must never repeat a received command.
    const accepted = inFlight;
    inFlight = null;
    if (accepted.session !== sessionId || accepted.session !== await $.session.id()) return;
    binding = reply.binding;
    for (const command of reply.commands) {
      try { await dispatch($, command); }
      catch (error) { acknowledge(command, 'unknown', error.message); }
    }
  } catch {
    transport = null;
  } finally { polling = false; }
}
