'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const azurelib3 = require('./core/provider-adapter/azurelib3_adapter.js');

function validAnimationDocument() {
  return {
    format_version: '1.8.0',
    includes: [{
      file_id: 'factory:shared/locomotion.animation.json',
      animations: ['animation.factory.walk'],
    }],
    animations: {
      'animation.factory.idle': {
        animation_length: 1.25,
        loop: true,
        bones: {
          root: {
            position: [0, 0, 0],
            rotation: {
              '0': {vector: [0, 0, 0], easing: 'easeInOutSine'},
              '0.5': {post: [0, 15, 0], lerp_mode: 'catmullrom'},
            },
            scale: {vector: [1, 1, 1], easing: 'easeOutBack', easingArgs: [1.70158]},
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

test('PR7 authority separates physical AzureLib runtime from the independently audited Blockbench plugin', () => {
  assert.deepEqual(azurelib3.AZURELIB3_AUTHORITY, {
    providerFamily: 'azurelib',
    runtimeVersion: '3.1.11',
    runtimeSource: 'AzureDoom/AzureLib',
    runtimeRef: '74ca485d43089c6953492ae7a10fc896eda30385',
    blockbenchPluginId: 'azurelib_utils',
    blockbenchPluginVersion: '2.1.5',
    blockbenchPluginSource: 'AzureDoom/AzureLib',
    blockbenchPluginRef: '4aac02dcefff5440874b3ec64871a1cd0feffadf',
    blockbenchFormatId: 'azure_model',
    animationFormatVersion: '1.8.0',
  });
});

test('animation validation accepts runtime-proven AzureLib 3.1.11 transforms, includes, easings and effect channels without mutation', () => {
  const input = validAnimationDocument();
  const before = JSON.stringify(input);
  const result = azurelib3.validateAzureLib3AnimationDocument(input);

  assert.equal(result.ok, true);
  assert.equal(result.animationCount, 1);
  assert.equal(result.includeCount, 1);
  assert.deepEqual(result.effectCounts, {sound: 1, particle: 1, timeline: 1});
  assert.equal(JSON.stringify(input), before);
});

test('runtime-proven custom easing names are accepted case-insensitively while unknown names fail closed instead of silently degrading to linear', () => {
  for (const easing of [
    'linear', 'step', 'easeInSine', 'easeOutQuad', 'easeInOutCubic',
    'easeInQuart', 'easeOutQuint', 'easeInOutExpo', 'easeInCirc',
    'easeOutBack', 'easeInOutElastic', 'easeInBounce', 'bezier',
    'bezier_after', 'catmullrom',
  ]) {
    const input = validAnimationDocument();
    input.animations['animation.factory.idle'].bones.root.scale = {vector: [1, 1, 1], easing};
    assert.equal(azurelib3.validateAzureLib3AnimationDocument(input).ok, true, easing);
  }

  const input = validAnimationDocument();
  input.animations['animation.factory.idle'].bones.root.scale.easing = 'totallyUnknownCurve';
  assert.throws(
    () => azurelib3.validateAzureLib3AnimationDocument(input),
    (error) => error?.code === 'UNSUPPORTED_AZURELIB3_EASING',
  );
});

test('sound and particle timestamps reject multiple payload arrays because AzureLib 3.1.11 runtime adapters require one JSON object per timestamp', () => {
  for (const channel of ['sound_effects', 'particle_effects']) {
    const input = validAnimationDocument();
    input.animations['animation.factory.idle'][channel]['0.5'] = [
      {effect: 'factory:first'},
      {effect: 'factory:second'},
    ];
    assert.throws(
      () => azurelib3.validateAzureLib3AnimationDocument(input),
      (error) => error?.code === 'UNSUPPORTED_AZURELIB3_MULTI_EFFECT_PAYLOAD',
      channel,
    );
  }
});

test('animation_scripts and plugin-only UUID metadata are rejected as runtime-unproven semantics', () => {
  const scripts = validAnimationDocument();
  scripts.animations['animation.factory.idle'].animation_scripts = {'0.5': 'factory:script'};
  assert.throws(
    () => azurelib3.validateAzureLib3AnimationDocument(scripts),
    (error) => error?.code === 'UNPROVEN_AZURELIB3_RUNTIME_FIELD',
  );

  const uuid = validAnimationDocument();
  uuid.animations['animation.factory.idle'].sound_effects['0.25'].uuid = 'editor-only-id';
  assert.throws(
    () => azurelib3.validateAzureLib3AnimationDocument(uuid),
    (error) => error?.code === 'UNPROVEN_AZURELIB3_RUNTIME_FIELD',
  );
});

test('effect serialization maps generic markers only to runtime-proven AzureLib channels', () => {
  assert.deepEqual(
    azurelib3.serializeAzureLib3EffectMarker(
      {time: 0.25, markerType: 'sound'},
      {effect: 'factory:test_sound'},
    ),
    {channel: 'sound_effects', time: '0.25', value: {effect: 'factory:test_sound'}},
  );

  assert.deepEqual(
    azurelib3.serializeAzureLib3EffectMarker(
      {time: 0.5, markerType: 'particle'},
      {effect: 'factory:test_particle', locator: 'muzzle', preEffectScript: 'variable.power = 1;'},
    ),
    {
      channel: 'particle_effects',
      time: '0.5',
      value: {effect: 'factory:test_particle', locator: 'muzzle', pre_effect_script: 'variable.power = 1;'},
    },
  );

  assert.deepEqual(
    azurelib3.serializeAzureLib3EffectMarker(
      {time: 0.75, markerType: 'timeline'},
      {instruction: ['factory:first', 'factory:second']},
    ),
    {channel: 'timeline', time: '0.75', value: ['factory:first', 'factory:second']},
  );

  assert.throws(
    () => azurelib3.serializeAzureLib3EffectMarker(
      {time: 1, markerType: 'script'},
      {instruction: 'factory:script'},
    ),
    (error) => error?.code === 'UNSUPPORTED_AZURELIB3_EFFECT_MARKER',
  );
});

test('export plan preserves bbmodel authority, forbids cross-provider conversion and stages only relative AzureLib artifacts', () => {
  assert.deepEqual(
    azurelib3.createAzureLib3ExportPlan({
      profileId: 'azurelib_entity',
      sourcePath: 'C:\\Users\\Gustavo\\factory_test.bbmodel',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    }),
    {
      providerFamily: 'azurelib',
      profileId: 'azurelib_entity',
      sourcePath: 'C:/Users/Gustavo/factory_test.bbmodel',
      preserveSource: true,
      artifacts: [
        {kind: 'model', path: 'staging/factory_test/factory_test.geo.json'},
        {kind: 'animation', path: 'staging/factory_test/factory_test.animation.json'},
      ],
      runtimeEvidence: 'UNPROVEN',
    },
  );

  assert.throws(
    () => azurelib3.createAzureLib3ExportPlan({
      profileId: 'geckolib4_entity',
      sourcePath: 'authoring/factory_test.bbmodel',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    }),
    (error) => error?.code === 'INVALID_AZURELIB3_PROFILE',
  );

  assert.throws(
    () => azurelib3.createAzureLib3ExportPlan({
      profileId: 'azurelib_entity',
      sourcePath: 'authoring/factory_test.bbmodel',
      outputDirectory: 'C:\\escape\\staging',
      resourceName: 'factory_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'INVALID_AZURELIB3_PATH',
  );
});
