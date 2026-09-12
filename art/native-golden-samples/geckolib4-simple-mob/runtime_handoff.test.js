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
  const clientProof = readRuntimeSource('GoldenSampleMobClientRuntimeProof.java');
  const gameTest = readRuntimeSource('GoldenSampleMobGameTest.java');
  const clientRuntime = client + '\n' + clientProof;

  assert.match(entity, /implements GeoEntity/);
  assert.match(entity, /GeckoLibUtil\.createInstanceCache\(this\)/);
  assert.match(entity, /animation\.golden_sample_mob\.idle/);
  assert.match(entity, /animation\.golden_sample_mob\.walk/);
  assert.match(entity, /registerControllers\(AnimatableManager\.ControllerRegistrar controllers\)/);
  assert.match(clientRuntime, /DefaultedEntityGeoModel/);
  assert.match(clientRuntime, /golden_sample_mob/);
  assert.match(client, /GoldenSampleMobClientRuntimeProof::createRenderer/);
  assert.match(gameTest, /@GameTest/);
  assert.match(gameTest, /GoldenSampleMob/);
});

test('runtime proof records durable target-exact server and live-client evidence', () => {
  const manifest = readJson('MANIFEST.json');
  const evidence = manifest.realHandoff.runtimeEvidence;

  assert.equal(manifest.realHandoff.reopenValidated, true);
  assert.equal(manifest.realHandoff.runtimeValidated, true);
  assert.equal(manifest.realHandoff.f4I6Evidence, true);
  assert.equal(manifest.state, 'REAL_HANDOFF_VALIDATED');
  assert.equal(evidence.classification, 'PASS');
  assert.equal(evidence.commit, '33f0322fd806d593da4e3063db93b709dbe878da');
  assert.equal(evidence.workflowRunId, 34710808440);
  assert.equal(evidence.jobId, 103599143647);
  assert.deepEqual(evidence.target, {
    minecraft: '1.21.1',
    neoforge: '21.1.248',
    java: 21,
    geckolib: '4.9.2',
  });
  assert.equal(evidence.server.gameTest, 'PASS');
  assert.equal(evidence.server.player_connected, true);
  assert.equal(evidence.server.mob_spawned, true);
  assert.equal(evidence.client.client_joined, true);
  assert.equal(evidence.client.renderer_invoked, true);
  assert.equal(evidence.client.baked_model_observed, true);
  assert.equal(evidence.client.texture_resolved, true);
  assert.equal(evidence.client.animation_motion_observed, true);
});

require('./client_runtime_handoff.test.js');
