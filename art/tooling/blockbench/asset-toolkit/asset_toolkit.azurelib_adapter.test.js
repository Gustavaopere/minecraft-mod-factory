'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const azurelib = require('./core/provider-adapter/azurelib_adapter.js');

function validGeoDocument(formatVersion = '1.12.0') {
  return {
    format_version: formatVersion,
    'minecraft:geometry': [{
      description: {
        identifier: 'geometry.factory_azure_test',
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
    includes: [{
      file_id: 'factory:animations/shared.animation.json',
      animations: ['animation.factory.shared'],
    }],
    animations: {
      'animation.factory_azure_test.idle': {
        animation_length: 1.25,
        loop: 'hold_on_last_frame',
        bones: {
          root: {
            position: [0, 0, 0],
            rotation: {
              '0': [0, 0, 0],
              '0.125': {vector: [0, 5, 0], easing: 'easeInSine'},
              '0.25': {vector: ['query.anim_time * 10', 10, 0]},
              '0.5': {post: [0, 15, 0], lerp_mode: 'catmullrom'},
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
          '0.75': ['factory:first_instruction', 'factory:second_instruction'],
        },
      },
    },
  };
}

test('PR7 authority pins AzureLib 3.1.11 and AzureLib Animator 2.1.5 to audited source refs', () => {
  assert.deepEqual(azurelib.AZURELIB_AUTHORITY, {
    providerFamily: 'azurelib',
    runtimeVersion: '3.1.11',
    runtimeSource: 'AzureDoom/AzureLib',
    runtimeRef: '4aac02dcefff5440874b3ec64871a1cd0feffadf',
    blockbenchPluginId: 'azurelib_utils',
    blockbenchPluginVersion: '2.1.5',
    blockbenchPluginSource: 'JannisX11/blockbench-plugins',
    blockbenchPluginRef: '38862eb66b219995b09926488f7d1084a0fb6b3a',
    blockbenchFormatId: 'azure_model',
    animationCodecId: 'azure_animation',
    animationFormatVersion: '1.8.0',
  });
});

test('geo validation accepts AzureLib runtime-supported format versions and both locator representations without mutation', () => {
  for (const formatVersion of ['1.12.0', '1.14.0', '1.21.0']) {
    const input = validGeoDocument(formatVersion);
    const before = JSON.stringify(input);
    const result = azurelib.validateAzureLibGeoDocument(input);
    assert.equal(result.ok, true);
    assert.equal(result.formatVersion, formatVersion);
    assert.equal(result.geometryCount, 1);
    assert.equal(result.locatorCount, 2);
    assert.equal(JSON.stringify(input), before);
  }
});

test('geo validation fails closed for unsupported formats and leaked authoring-only IK metadata', () => {
  assert.throws(
    () => azurelib.validateAzureLibGeoDocument(validGeoDocument('1.21.20')),
    (error) => error?.code === 'UNSUPPORTED_AZURELIB_GEO_FORMAT',
  );

  const leaked = validGeoDocument();
  leaked.azureIKChains = [{name: 'leg'}];
  assert.throws(
    () => azurelib.validateAzureLibGeoDocument(leaked),
    (error) => error?.code === 'AZURELIB_AUTHORING_METADATA_IN_RUNTIME_ARTIFACT',
  );
});

test('geo validation rejects malformed AzureLib locator payloads', () => {
  const input = validGeoDocument();
  input['minecraft:geometry'][0].bones[0].locators.muzzle = {
    ignore_inherited_scale: 'yes',
    offset: [1, 2],
  };
  assert.throws(
    () => azurelib.validateAzureLibGeoDocument(input),
    (error) => error?.code === 'INVALID_AZURELIB_LOCATOR',
  );
});

test('animation validation accepts AzureLib 1.8.0 transforms, custom easing, Bedrock lerp, includes and effect channels', () => {
  const input = validAnimationDocument();
  const before = JSON.stringify(input);
  const result = azurelib.validateAzureLibAnimationDocument(input);
  assert.equal(result.ok, true);
  assert.equal(result.formatVersion, '1.8.0');
  assert.equal(result.animationCount, 1);
  assert.equal(result.includeCount, 1);
  assert.deepEqual(result.effectCounts, {sound: 1, particle: 1, timeline: 1});
  assert.equal(JSON.stringify(input), before);
});

test('animation validation preserves known built-in AzureLib loop semantics and fails closed for unaudited custom loop names', () => {
  for (const loop of [false, true, 'false', 'true', 'play_once', 'loop', 'hold_on_last_frame']) {
    const input = validAnimationDocument();
    input.animations['animation.factory_azure_test.idle'].loop = loop;
    assert.equal(azurelib.validateAzureLibAnimationDocument(input).ok, true, String(loop));
  }

  const custom = validAnimationDocument();
  custom.animations['animation.factory_azure_test.idle'].loop = 'factory:custom_loop';
  assert.throws(
    () => azurelib.validateAzureLibAnimationDocument(custom),
    (error) => error?.code === 'UNSUPPORTED_AZURELIB_LOOP',
  );
});

test('animation validation rejects duplicate include ownership instead of relying on runtime first-wins warnings', () => {
  const input = validAnimationDocument();
  input.includes.push({
    file_id: 'factory:animations/other.animation.json',
    animations: ['animation.factory.shared'],
  });
  assert.throws(
    () => azurelib.validateAzureLibAnimationDocument(input),
    (error) => error?.code === 'DUPLICATE_AZURELIB_INCLUDE_ANIMATION',
  );
});

test('animation validation rejects authoring-only FABRIK state in runtime animation artifacts', () => {
  const input = validAnimationDocument();
  input.azureIKChains = [{name: 'leg'}];
  assert.throws(
    () => azurelib.validateAzureLibAnimationDocument(input),
    (error) => error?.code === 'AZURELIB_AUTHORING_METADATA_IN_RUNTIME_ARTIFACT',
  );
});

test('effect serialization maps generic markers onto AzureLib runtime channels without hiding provider data in labels', () => {
  assert.deepEqual(
    azurelib.serializeAzureLibEffectMarker(
      {time: 0.25, markerType: 'sound', label: 'audio cue'},
      {effect: 'factory:test_sound'},
    ),
    {channel: 'sound_effects', time: '0.25', value: {effect: 'factory:test_sound'}},
  );

  assert.deepEqual(
    azurelib.serializeAzureLibEffectMarker(
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
    azurelib.serializeAzureLibEffectMarker(
      {time: 0.75, markerType: 'timeline', label: 'timeline cue'},
      {instruction: ['factory:first_instruction', 'factory:second_instruction']},
    ),
    {
      channel: 'timeline',
      time: '0.75',
      value: ['factory:first_instruction', 'factory:second_instruction'],
    },
  );
});

test('unsupported abstract effect markers fail closed until an explicit AzureLib mapping exists', () => {
  assert.throws(
    () => azurelib.serializeAzureLibEffectMarker(
      {time: 0, markerType: 'custom', label: 'opaque'},
      {instruction: 'opaque'},
    ),
    (error) => error?.code === 'UNSUPPORTED_AZURELIB_EFFECT_MARKER',
  );
});

test('export plan preserves bbmodel authority and stages only AzureLib runtime artifacts', () => {
  assert.deepEqual(
    azurelib.createAzureLibExportPlan({
      profileId: 'azurelib_entity',
      sourcePath: 'authoring/factory_azure_test.bbmodel',
      outputDirectory: 'staging/factory_azure_test',
      resourceName: 'factory_azure_test',
      includeAnimations: true,
    }),
    {
      providerFamily: 'azurelib',
      profileId: 'azurelib_entity',
      sourcePath: 'authoring/factory_azure_test.bbmodel',
      preserveSource: true,
      artifacts: [
        {kind: 'model', path: 'staging/factory_azure_test/factory_azure_test.geo.json'},
        {kind: 'animation', path: 'staging/factory_azure_test/factory_azure_test.animation.json'},
      ],
      runtimeEvidence: 'UNPROVEN',
    },
  );

  assert.throws(
    () => azurelib.createAzureLibExportPlan({
      profileId: 'azurelib_entity',
      sourcePath: 'authoring/factory_azure_test.geo.json',
      outputDirectory: 'staging/factory_azure_test',
      resourceName: 'factory_azure_test',
      includeAnimations: true,
    }),
    (error) => error?.code === 'AZURELIB_SOURCE_MUST_BE_BBMODEL',
  );
});

test('export plan rejects cross-provider profiles and unsafe output paths', () => {
  assert.throws(
    () => azurelib.createAzureLibExportPlan({
      profileId: 'geckolib4_entity',
      sourcePath: 'authoring/factory_azure_test.bbmodel',
      outputDirectory: 'staging/factory_azure_test',
      resourceName: 'factory_azure_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'INVALID_AZURELIB_PROFILE',
  );

  assert.throws(
    () => azurelib.createAzureLibExportPlan({
      profileId: 'azurelib_entity',
      sourcePath: 'C:\\Users\\Gustavo\\Minecraft\\factory_azure_test.bbmodel',
      outputDirectory: 'C:\\Users\\Gustavo\\Minecraft\\staging',
      resourceName: 'factory_azure_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'INVALID_AZURELIB_PATH',
  );
});
