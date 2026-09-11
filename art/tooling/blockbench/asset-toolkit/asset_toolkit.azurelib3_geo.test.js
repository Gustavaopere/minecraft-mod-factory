'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const azurelib3 = require('./core/provider-adapter/azurelib3_adapter.js');

function validGeoDocument(formatVersion = '1.12.0') {
  return {
    format_version: formatVersion,
    'minecraft:geometry': [{
      description: {
        identifier: 'geometry.factory_test',
        texture_width: 16,
        texture_height: 16,
      },
      bones: [{
        name: 'root',
        pivot: [0, 0, 0],
        cubes: [],
        locators: {muzzle: [1, 2, 3]},
      }],
    }],
  };
}

test('AzureLib 3.1.11 geo validator accepts only the runtime-enumerated Bedrock geometry format versions without mutation', () => {
  for (const formatVersion of ['1.12.0', '1.14.0', '1.21.0']) {
    const input = validGeoDocument(formatVersion);
    const before = JSON.stringify(input);
    assert.deepEqual(azurelib3.validateAzureLib3GeoDocument(input), {
      ok: true,
      formatVersion,
      geometryCount: 1,
      boneCount: 1,
    });
    assert.equal(JSON.stringify(input), before);
  }
});

test('AzureLib 3.1.11 geo validator fails closed on unenumerated format versions and malformed minecraft:geometry roots', () => {
  assert.throws(
    () => azurelib3.validateAzureLib3GeoDocument(validGeoDocument('1.21.20')),
    (error) => error?.code === 'UNSUPPORTED_AZURELIB3_GEO_FORMAT',
  );

  assert.throws(
    () => azurelib3.validateAzureLib3GeoDocument({format_version: '1.21.0', 'minecraft:geometry': []}),
    (error) => error?.code === 'INVALID_AZURELIB3_GEO_DOCUMENT',
  );

  const malformedBones = validGeoDocument('1.21.0');
  malformedBones['minecraft:geometry'][0].bones = {};
  assert.throws(
    () => azurelib3.validateAzureLib3GeoDocument(malformedBones),
    (error) => error?.code === 'INVALID_AZURELIB3_GEO_DOCUMENT',
  );
});

test('AzureLib 3.1.11 geo validator rejects authoring-only IK metadata from runtime artifacts', () => {
  const leaked = validGeoDocument('1.21.0');
  leaked.azureIKChains = [{name: 'leg'}];
  assert.throws(
    () => azurelib3.validateAzureLib3GeoDocument(leaked),
    (error) => error?.code === 'UNPROVEN_AZURELIB3_RUNTIME_FIELD',
  );
});
