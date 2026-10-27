import { expect, test } from 'claude-code/testing';
import { base } from './helpers';

test('owner input is preserved exactly', async ($, on) => {
  on('prompt.submit', ($, e) => ({ text: e.text, origin: e.origin }));
  const result = await $.prompt.submit({ text: 'Owner draft', asUser: true });
  expect(result.text).toBe('Owner draft');
});
