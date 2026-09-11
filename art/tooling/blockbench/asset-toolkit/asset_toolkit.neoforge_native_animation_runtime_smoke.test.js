'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');

function runtimeSmokeSource() {
  return {
    length: 1.125,
    loop: 'loop',
    channels: [
      {
        bone: 'head',
        channel: 'rotation',
        keyframes: [
          {time: 0, value: [0, 0, 0], easing: 'linear'},
          {time: 0.5, value: [22.5, 0, 0], easing: 'linear'},
        ],
      },
    ],
  };
}

test('PR8 target-exact runtime smoke consumes the exact Factory serializer document at the planned NeoForge resource path', () => {
  const plan = core.createNeoForgeNativeAnimationExportPlan({
    profileId: 'neoforge_native_entity_animation',
    sourcePath: 'runtime-smoke-authority.bbmodel',
    namespace: 'factorypr8',
    resourceName: 'native_smoke',
  });
  assert.equal(plan.outputPath, 'assets/factorypr8/neoforge/animations/entity/native_smoke.json');

  const serialized = core.serializeNeoForgeNativeAnimation(runtimeSmokeSource());
  const fixture = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'runtime-smoke', 'native-smoke.json'),
    'utf8',
  ));

  assert.deepEqual(fixture, serialized);
  assert.equal(core.validateNeoForgeNativeAnimationDocument(fixture).ok, true);
});
