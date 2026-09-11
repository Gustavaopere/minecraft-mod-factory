'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const adapterPath = path.resolve(__dirname, 'core/provider-adapter/azurelib3_adapter.js');

test('PR7 materializes the AzureLib 3 core provider adapter module', () => {
  assert.equal(
    fs.existsSync(adapterPath),
    true,
    'core/provider-adapter/azurelib3_adapter.js must exist before behavioral contract tests run',
  );
});
