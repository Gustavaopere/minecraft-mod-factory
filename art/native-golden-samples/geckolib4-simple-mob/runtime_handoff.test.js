'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;
const RUNTIME_SMOKE = path.join(ROOT, 'runtime-smoke');
const RUNTIME_TESTS = path.join(RUNTIME_SMOKE, 'tests');

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relativePath), 'utf8'));
}

function readRuntimeSource(fileName) {
  return fs.readFileSync(path.join(RUNTIME_TESTS, fileName), 'utf8');
}

test('runtime smoke contract pins the exact physical target and audited GeckoLib authority', () => {
  const contract = readJson('runtime-smoke/contract.json');

  assert.deepEqual(contract.target, {
    minecraft: '1.21.1',
    neoforge: '21.1.248',
    java: 21,
  });
  assert.deepEqual(contract.geckolib, {
    version: '4.9.2',
    source: 'bernie-g/geckolib',
    ref: 'd57fc640de083ae67ec0051a02b2b4fb22f4d02b',
    mavenRepository: 'https://dl.cloudsmith.io/public/geckolib3/geckolib/maven/',
    coordinate: 'software.bernie.geckolib:geckolib-neoforge-1.21.1:4.9.2',
  });
});

test('runtime smoke packages the real Blockbench exports under GeckoLib default entity resource paths', () => {
  const contract = readJson('runtime-smoke/contract.json');

  assert.deepEqual(contract.resources, {
    model: {
      source: '../actual/golden_sample_mob.geo.json',
      target: 'assets/i3_golden_mod/geo/entity/golden_sample_mob.geo.json',
      sha256: 'e3627d896e3bc8c30f7b10c930ba5c70dc4f931191c9cc13e0449404e541e889',
    },
    animation: {
      source: '../actual/golden_sample_mob.animation.json',
      target: 'assets/i3_golden_mod/animations/entity/golden_sample_mob.animation.json',
      sha256: 'da77cb8c6d8b44610eab3bc135a0b6f645b2b29783dd552f1a471e05c1a262aa',
    },
    texture: {
      source: '../golden-sample-mob.png',
      target: 'assets/i3_golden_mod/textures/entity/golden_sample_mob.png',
      sha256: 'c93b4a2d460bf10a5a127f8f76238e054e1e3a7c2ad84128a07bb21e6ee0f19b',
    },
  });
});

test('runtime Java fixture binds the physical animation names and GeckoLib 4.9.2 APIs', () => {
  const entity = readRuntimeSource('GoldenSampleMob.java');
  const client = readRuntimeSource('GoldenSampleMobClient.java');
  const gameTest = readRuntimeSource('GoldenSampleMobGameTest.java');

  assert.match(entity, /implements GeoEntity/);
  assert.match(entity, /GeckoLibUtil\.createInstanceCache\(this\)/);
  assert.match(entity, /animation\.golden_sample_mob\.idle/);
  assert.match(entity, /animation\.golden_sample_mob\.walk/);
  assert.match(entity, /registerControllers\(AnimatableManager\.ControllerRegistrar controllers\)/);
  assert.match(client, /DefaultedEntityGeoModel/);
  assert.match(client, /golden_sample_mob/);
  assert.match(gameTest, /@GameTest/);
  assert.match(gameTest, /GoldenSampleMob/);
});

test('runtime proof remains fail-closed until live client validation is recorded', () => {
  const manifest = readJson('MANIFEST.json');

  assert.equal(manifest.realHandoff.reopenValidated, true);
  assert.equal(manifest.realHandoff.runtimeValidated, false);
  assert.equal(manifest.realHandoff.f4I6Evidence, false);
  assert.equal(manifest.state, 'PREPARED_FOR_REAL_HANDOFF');
});
