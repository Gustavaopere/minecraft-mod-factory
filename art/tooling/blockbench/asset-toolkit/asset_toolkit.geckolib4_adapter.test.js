'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const geckolib4 = require('./core/provider-adapter/geckolib4_adapter.js');

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
        locators: {
          muzzle: [1, 2, 3],
          rotated_anchor: {
            ignore_inherited_scale: true,
            offset: [4, 5, 6],
            rotation: [0, 90, 0],
          },
        },
      }],
    }],
  };
}

function validAnimationDocument() {
  return {
    format_version: '1.8.0',
    animations: {
      'animation.factory_test.idle': {
        animation_length: 1.25,
        loop: true,
        bones: {
          root: {
            position: [0, 0, 0],
            rotation: {
              '0.0': [0, 0, 0],
              '0.5': {vector: [0, 15, 0], easing: 'linear'},
            },
            scale: [1, 1, 1],
          },
        },
        sound_effects: {
          '0.25': {effect: 'factory:test_sound'},
        },
        particle_effects: {
          '0.5': {
            effect: 'factory:test_particle',
            locator: 'muzzle',
            pre_effect_script: 'variable.power = 1;',
          },
        },
        timeline: {
          '0.75': 'factory:custom_instruction',
        },
      },
    },
  };
}

test('PR6 authority pins the audited Blockbench plugin and physical GeckoLib runtime exactly', () => {
  assert.deepEqual(geckolib4.GECKOLIB4_AUTHORITY, {
    providerFamily: 'geckolib4',
    runtimeVersion: '4.9.2',
    runtimeSource: 'bernie-g/geckolib',
    runtimeRef: 'd57fc640de083ae67ec0051a02b2b4fb22f4d02b',
    blockbenchPluginId: 'geckolib',
    blockbenchPluginVersion: '4.2.5',
    blockbenchPluginSource: 'JannisX11/blockbench-plugins',
    blockbenchPluginRef: '96d3b694de7d44077de68181711816153c442a6f',
  });
});

test('geo validation accepts runtime-supported format versions and both locator representations without mutating input', () => {
  for (const formatVersion of ['1.12.0', '1.14.0', '1.21.0']) {
    const input = validGeoDocument(formatVersion);
    const before = JSON.stringify(input);
    const result = geckolib4.validateGeckoLib4GeoDocument(input);
    assert.equal(result.ok, true);
    assert.equal(result.formatVersion, formatVersion);
    assert.equal(result.geometryCount, 1);
    assert.equal(result.locatorCount, 2);
    assert.equal(JSON.stringify(input), before);
  }
});

test('geo validation rejects Blockbench 1.21.20 output instead of pretending GeckoLib 4.9.2 accepts it', () => {
  assert.throws(
    () => geckolib4.validateGeckoLib4GeoDocument(validGeoDocument('1.21.20')),
    (error) => error?.code === 'UNSUPPORTED_GECKOLIB4_GEO_FORMAT',
  );
});

test('geo validation rejects malformed locator payloads', () => {
  const input = validGeoDocument();
  input['minecraft:geometry'][0].bones[0].locators.muzzle = 'not-a-locator';
  assert.throws(
    () => geckolib4.validateGeckoLib4GeoDocument(input),
    (error) => error?.code === 'INVALID_GECKOLIB4_LOCATOR',
  );
});

test('animation validation accepts GeckoLib 4.9.2 transforms, loop modes, easing and effect channels', () => {
  const input = validAnimationDocument();
  const before = JSON.stringify(input);
  const result = geckolib4.validateGeckoLib4AnimationDocument(input);
  assert.equal(result.ok, true);
  assert.equal(result.animationCount, 1);
  assert.deepEqual(result.effectCounts, {sound: 1, particle: 1, timeline: 1});
  assert.equal(JSON.stringify(input), before);
});

test('effect serialization maps provider data to GeckoLib runtime channel names without hiding payload in label', () => {
  assert.deepEqual(
    geckolib4.serializeGeckoLib4EffectMarker(
      {time: 0.25, markerType: 'sound', label: 'audio cue'},
      {effect: 'factory:test_sound'},
    ),
    {channel: 'sound_effects', time: '0.25', value: {effect: 'factory:test_sound'}},
  );

  assert.deepEqual(
    geckolib4.serializeGeckoLib4EffectMarker(
      {time: 0.5, markerType: 'particle', label: 'vfx cue'},
      {effect: 'factory:test_particle', locator: 'muzzle', preEffectScript: 'variable.power = 1;'},
    ),
    {
      channel: 'particle_effects',
      time: '0.5',
      value: {effect: 'factory:test_particle', locator: 'muzzle', pre_effect_script: 'variable.power = 1;'},
    },
  );

  assert.deepEqual(
    geckolib4.serializeGeckoLib4EffectMarker(
      {time: 0.75, markerType: 'timeline', label: 'timeline cue'},
      {instruction: 'factory:custom_instruction'},
    ),
    {channel: 'timeline', time: '0.75', value: 'factory:custom_instruction'},
  );
});

test('unsupported abstract custom markers fail closed until an explicit GeckoLib mapping exists', () => {
  assert.throws(
    () => geckolib4.serializeGeckoLib4EffectMarker(
      {time: 0, markerType: 'custom', label: 'opaque'},
      {instruction: 'opaque'},
    ),
    (error) => error?.code === 'UNSUPPORTED_GECKOLIB4_EFFECT_MARKER',
  );
});

test('export plan preserves bbmodel authority and only stages provider artifacts', () => {
  assert.deepEqual(
    geckolib4.createGeckoLib4ExportPlan({
      profileId: 'geckolib4_entity',
      sourcePath: 'authoring/factory_test.bbmodel',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    }),
    {
      providerFamily: 'geckolib4',
      profileId: 'geckolib4_entity',
      sourcePath: 'authoring/factory_test.bbmodel',
      preserveSource: true,
      artifacts: [
        {kind: 'model', path: 'staging/factory_test/factory_test.geo.json'},
        {kind: 'animation', path: 'staging/factory_test/factory_test.animation.json'},
      ],
      runtimeEvidence: 'UNPROVEN',
    },
  );

  assert.throws(
    () => geckolib4.createGeckoLib4ExportPlan({
      profileId: 'geckolib4_entity',
      sourcePath: 'authoring/factory_test.geo.json',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    }),
    (error) => error?.code === 'GECKOLIB4_SOURCE_MUST_BE_BBMODEL',
  );
});

test('export plan rejects Windows drive-absolute staging paths as non-relative output', () => {
  assert.throws(
    () => geckolib4.createGeckoLib4ExportPlan({
      profileId: 'geckolib4_entity',
      sourcePath: 'C:\\Users\\Gustavo\\Minecraft\\factory_test.bbmodel',
      outputDirectory: 'C:\\Users\\Gustavo\\Minecraft\\staging',
      resourceName: 'factory_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'INVALID_GECKOLIB4_PATH',
  );
});
