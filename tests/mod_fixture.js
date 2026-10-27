const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function fixture(fetch) {
  const calls = [];
  const context = vm.createContext({Math, JSON});
  const source = ['state', 'wire', 'submission', 'controls', 'transport']
    .map(name => fs.readFileSync(path.join(__dirname, '../mod/src', name + '.js'), 'utf8')).join('\n');
  vm.runInContext(source + '\nObject.assign(globalThis, {tick, refresh, emit, acknowledge});', context);
  const $ = {
    fs: {read: async () => JSON.stringify({url: 'http://127.0.0.1:39086', token: 'synthetic'})},
    clock: {now: async () => 100},
    session: Object.fromEntries(Object.entries({id: 'session-a', cwd: '/workspace', root: '/workspace',
      model: 'synthetic', version: {}, surfaces: ['vscode'], usage: {}})
      .map(([key, value]) => [key, async () => value])),
    http: {fetch: async (_url, options) => fetch(JSON.parse(options.body))},
    prompt: {submit: async body => { calls.push(body); return {}; }}
  };
  return {context, $, calls, tick: () => context.tick($), value: expression => vm.runInContext(expression, context)};
}

function reply(body, commands = []) {
  return {ok: true, text: JSON.stringify({ok: true, binding: 'binding-a', batch: body.batch, commands})};
}
module.exports = {fixture, reply};
