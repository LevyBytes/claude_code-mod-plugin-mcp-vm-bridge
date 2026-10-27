import { mock } from 'claude-code/testing';
export function base(on, transport) {
  const clock = mock.clock(on);
  on('session.start', () => ({ cwd: '/workspace' }));
  on('session.id', () => ({ value: 'session-a' }));
  on('session.cwd', () => ({ value: '/workspace' }));
  on('session.root', () => ({ value: '/workspace' }));
  on('session.model', () => ({ value: 'model-test' }));
  on('session.version', () => ({ value: { version: '2.1.310' } }));
  on('session.surfaces', () => ({ value: ['vscode'] }));
  on('session.usage', () => ({ value: { context: { window: 200000 }, rateLimits: [] } }));
  on('fs.read', () => ({ value: JSON.stringify({ url: 'http://127.0.0.1:39086', token: 'synthetic' }) }));
  on('http.fetch', ($, e) => ({ value: { ok: true, status: 200,
    text: JSON.stringify({ batch: JSON.parse(e.init.body).batch, ...transport(JSON.parse(e.init.body)) }) } }));
  return clock;
}
