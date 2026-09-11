'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');

const ROOT = __dirname;
const JAVA_FIXTURE = path.join(ROOT, 'runtime-smoke', 'AnimatedJavaDatapackRuntimeSmokeTest.java');
const FUNCTION_FIXTURE = path.join(ROOT, 'runtime-smoke', 'pr11-summon.mcfunction');

test('PR11 runtime smoke stays bound to the audited 1.21.1 Animated Java handoff', () => {
  const plan = core.createAnimatedJavaExportPlan({
    sourcePath: 'fixtures/cinematic.ajblueprint',
    blueprintId: 'factorypr11:runtime_smoke',
    targetMinecraftVersion: '1.21.1',
    resourcePackExportMode: 'folder',
    dataPackExportMode: 'folder',
    resourcePackPath: 'build/pr11-resource-pack',
    dataPackPath: 'build/pr11-data-pack',
    enablePluginMode: false,
  });

  assert.equal(plan.targetMinecraftVersion, '1.21.1');
  assert.equal(plan.blueprintFormatId, 'animated-java:format/blueprint');
  assert.equal(plan.blueprintCodecId, 'animated_java:codec/blueprint');
  assert.equal(plan.preserveSource, true);
  assert.equal(plan.runtimeEvidence, 'UNPROVEN');
  assert.equal(plan.runtimeValidated, false);
  assert.equal(plan.f4I6Evidence, false);

  const java = fs.readFileSync(JAVA_FIXTURE, 'utf8');
  assert.match(java, /performPrefixedCommand\(source, "function factorypr11:smoke\/summon"\)/);
  assert.match(java, /assertEntityPresent\(EntityType\.ITEM_DISPLAY, relativeSpawn\)/);

  const fn = fs.readFileSync(FUNCTION_FIXTURE, 'utf8').trim();
  assert.match(fn, /^summon minecraft:item_display ~ ~ ~ /);
  assert.match(fn, /Tags:\["factorypr11\.runtime_smoke"\]/);
  assert.match(fn, /teleport_duration:0/);
  assert.match(fn, /interpolation_duration:1/);
});
