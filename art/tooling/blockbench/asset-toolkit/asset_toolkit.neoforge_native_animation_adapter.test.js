'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');

function sampleRuntimeDocument() {
  return {
    length: 1.125,
    loop: true,
    animations: [
      {
        bone: 'head',
        target: 'rotation',
        keyframes: [
          {timestamp: 0, target: [0, 0, 0], interpolation: 'linear'},
          {timestamp: 0.5, target: [22.5, 0, 0], interpolation: 'catmullrom'},
        ],
      },
    ],
  };
}

function assertCoreFunction(name) {
  assert.equal(typeof core[name], 'function', `missing core.${name}`);
  return core[name];
}

test('PR8 pins the exact NeoForge 1.21.1 runtime and upstream Blockbench exporter provenance', () => {
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.minecraftVersion, '1.21.1');
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.neoforgeVersion, '21.1.248');
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.runtimeSource, 'neoforged/NeoForge');
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.runtimeRef, 'd8d64b44bb46323d44520fe27feda0a9a08c1c82');
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.animationRoot, 'neoforge/animations/entity');
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.blockbenchPluginId, 'animation_to_json');
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.blockbenchPluginVersion, '1.0.1');
  assert.equal(core.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.blockbenchPluginRef, '91ba2b80c895960fe93de87fd0c30f9b840f28f2');
});

test('PR8 validator accepts the exact built-in NeoForge 1.21.1 JSON animation contract and exporter aliases', () => {
  const validate = assertCoreFunction('validateNeoForgeNativeAnimationDocument');
  const result = validate(sampleRuntimeDocument());
  assert.deepEqual(result, {
    ok: true,
    length: 1.125,
    loop: true,
    channelCount: 1,
    keyframeCount: 2,
  });
});

test('PR8 validator fails closed for unproven custom targets, interpolations, and runtime fields', () => {
  const validate = assertCoreFunction('validateNeoForgeNativeAnimationDocument');

  const customTarget = sampleRuntimeDocument();
  customTarget.animations[0].target = 'example:custom_target';
  assert.throws(() => validate(customTarget), (error) => error?.code === 'UNPROVEN_NEOFORGE_NATIVE_ANIMATION_TYPE');

  const customInterpolation = sampleRuntimeDocument();
  customInterpolation.animations[0].keyframes[0].interpolation = 'example:spline';
  assert.throws(() => validate(customInterpolation), (error) => error?.code === 'UNPROVEN_NEOFORGE_NATIVE_ANIMATION_TYPE');

  const unknownField = sampleRuntimeDocument();
  unknownField.animations[0].keyframes[0].easing = 'linear';
  assert.throws(() => validate(unknownField), (error) => error?.code === 'UNPROVEN_NEOFORGE_NATIVE_ANIMATION_FIELD');
});

test('PR8 serializer maps the provider-neutral animation model to canonical NeoForge JSON', () => {
  const serialize = assertCoreFunction('serializeNeoForgeNativeAnimation');
  const document = serialize({
    length: 1.125,
    loop: 'loop',
    channels: [
      {
        bone: 'head',
        channel: 'rotation',
        keyframes: [
          {time: 0, value: [0, 0, 0], easing: 'linear'},
          {time: 0.5, value: [22.5, 0, 0], easing: 'catmullrom'},
        ],
      },
    ],
  });

  assert.deepEqual(document, {
    length: 1.125,
    loop: true,
    animations: [
      {
        bone: 'head',
        target: 'minecraft:rotation',
        keyframes: [
          {timestamp: 0, target: [0, 0, 0], interpolation: 'minecraft:linear'},
          {timestamp: 0.5, target: [22.5, 0, 0], interpolation: 'minecraft:catmullrom'},
        ],
      },
    ],
  });
});

test('PR8 serializer rejects provider-neutral features with no audited native NeoForge representation', () => {
  const serialize = assertCoreFunction('serializeNeoForgeNativeAnimation');

  assert.throws(() => serialize({
    length: 1,
    loop: 'hold',
    channels: [],
  }), (error) => error?.code === 'UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_LOOP_MODE');

  assert.throws(() => serialize({
    length: 1,
    loop: 'once',
    channels: [{
      bone: 'root',
      channel: 'rotation',
      keyframes: [{time: 0, value: [0, 0, 0], easing: 'bezier'}],
    }],
  }), (error) => error?.code === 'UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_INTERPOLATION');

  assert.throws(() => serialize({
    length: 1,
    loop: 'once',
    channels: [],
    effectMarkers: [{time: 0, markerType: 'sound'}],
  }), (error) => error?.code === 'UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_EFFECT_MARKERS');
});
