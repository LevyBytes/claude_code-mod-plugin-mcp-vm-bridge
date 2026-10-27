async function send($, command) {
  pendingSend = command.request_id;
  try {
    if (command.session_id !== await $.session.id()) throw new Error('Session changed');
    if (snapshot.state !== 'idle') throw new Error('Session no longer idle');
    if (typeof command.text !== 'string' || !command.text.trim() || command.text.length > 16000) {
      throw new Error('Invalid message');
    }
    const prefix = PREFIXES[command.source?.kind];
    if (!prefix) throw new Error('UNSUPPORTED_SENDER_IDENTITY');
    const result = await $.prompt.submit({ text: prefix + command.text });
    acknowledge(command, result?.drop ? 'dropped' : 'started', result?.drop || '');
  } catch (error) { acknowledge(command, 'rejected', error.message); }
  finally { if (pendingSend === command.request_id) pendingSend = false; }
}
