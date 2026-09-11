'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('./core/index.js');

test('PR9 authority matches the target-exact Easy Model Entities 2.3.0 API contract', () => {
  assert.equal(core.EASY_MODEL_ENTITIES_AUTHORITY?.schemaVersion, '0.2.0');
  assert.equal(core.EASY_MODEL_ENTITIES_AUTHORITY?.apiVersion, '2.3.0');
});
