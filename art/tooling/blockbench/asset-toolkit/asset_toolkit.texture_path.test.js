'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const toolkit = require('./core/index.js');

// TDD evidence: RED confirmed at da1b6cdd82dc3c8d344a80ebb4df61b350a4af52; GREEN validator and deterministic standalone verified from c5ba7562d658ebee3af34086a44b37ef0734d960.
test('external texture without a path is rejected', () => {
  const result = toolkit.validateProject({
    name: 'texture_path_contract',
    save_path: '/tmp/texture_path_contract.bbmodel',
    groups: [],
    elements: [],
    textures: [{
      name: 'external.png',
      uuid: 'tex-external',
      width: 16,
      height: 16,
      internal: false,
      path: '',
    }],
    animations: [],
  }, {});

  assert.ok(result.errors.some((item) => item.code === 'MISSING_EXTERNAL_TEXTURE_PATH'));
});
