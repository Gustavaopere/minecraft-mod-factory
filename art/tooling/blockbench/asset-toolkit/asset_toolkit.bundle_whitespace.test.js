'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {buildBundle} = require('./build_toolkit_bundle.js');

test('generated standalone bundle contains no whitespace-only lines', () => {
  const lines = buildBundle().split('\n');
  const offender = lines.findIndex((line) => /^[ \t]+$/.test(line));
  assert.equal(
    offender,
    -1,
    offender === -1 ? '' : `bundle line ${offender + 1} contains trailing indentation without content`,
  );
});
