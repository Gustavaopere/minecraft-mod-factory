'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const integration = require('./blockbench-plugin/geckolib4_adapter.js');

function geoDocument() {
  return {
    format_version: '1.12.0',
    'minecraft:geometry': [{
      description: {identifier: 'geometry.factory_test', texture_width: 16, texture_height: 16},
      bones: [{name: 'root', pivot: [0, 0, 0], locators: {muzzle: [1, 2, 3]}}],
    }],
  };
}

function animationDocument() {
  return {
    format_version: '1.8.0',
    animations: {
      'animation.factory_test.idle': {
        animation_length: 1,
        loop: true,
        bones: {root: {rotation: [0, 0, 0]}},
        sound_effects: {'0.25': {effect: 'factory:test_sound'}},
      },
    },
  };
}

function blockbenchMock(overrides = {}) {
  const calls = {modelCompile: 0, animationCompile: 0};
  const bb = {
    Blockbench: {
      isWeb: false,
      Project: {
        format: {id: 'geckolib_model'},
        save_path: 'authoring/factory_test.bbmodel',
      },
    },
    Codecs: {
      bedrock: {
        compile() {
          calls.modelCompile++;
          return JSON.stringify(geoDocument());
        },
      },
    },
    Animator: {
      buildFile() {
        calls.animationCompile++;
        return animationDocument();
      },
    },
  };
  return {bb: Object.assign(bb, overrides), calls};
}

test('Blockbench GeckoLib adapter requires an active source-native geckolib_model project', () => {
  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchGeckoLib4Adapter(bb);
  assert.equal(adapter.sourcePath(), 'authoring/factory_test.bbmodel');

  bb.Blockbench.Project.format.id = 'java_block';
  assert.throws(
    () => integration.createBlockbenchGeckoLib4Adapter(bb),
    (error) => error?.code === 'GECKOLIB4_PROJECT_FORMAT_REQUIRED',
  );

  bb.Blockbench.Project.format.id = 'geckolib_model';
  bb.Blockbench.Project.save_path = '';
  assert.throws(
    () => integration.createBlockbenchGeckoLib4Adapter(bb),
    (error) => error?.code === 'GECKOLIB4_SOURCE_NOT_SAVED',
  );
});

test('preview accepts absolute native Blockbench save paths while output staging stays relative', () => {
  for (const [sourcePath, expectedSourcePath] of [
    ['/home/gustavo/minecraft/factory_test.bbmodel', '/home/gustavo/minecraft/factory_test.bbmodel'],
    ['C:\\Users\\Gustavo\\Minecraft\\factory_test.bbmodel', 'C:/Users/Gustavo/Minecraft/factory_test.bbmodel'],
  ]) {
    const {bb} = blockbenchMock();
    bb.Blockbench.Project.save_path = sourcePath;
    const adapter = integration.createBlockbenchGeckoLib4Adapter(bb);
    assert.equal(adapter.sourcePath(), expectedSourcePath);
    const preview = adapter.previewExport({
      profileId: 'geckolib4_entity',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: false,
    });
    assert.equal(preview.plan.sourcePath, expectedSourcePath);
  }

  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchGeckoLib4Adapter(bb);
  assert.throws(
    () => adapter.previewExport({
      profileId: 'geckolib4_entity',
      outputDirectory: '/absolute/staging',
      resourceName: 'factory_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'INVALID_GECKOLIB4_PATH',
  );
});

test('preview compiles through the audited Blockbench hooks and validates provider documents without writing', () => {
  const {bb, calls} = blockbenchMock();
  const adapter = integration.createBlockbenchGeckoLib4Adapter(bb);
  const preview = adapter.previewExport({
    profileId: 'geckolib4_entity',
    outputDirectory: 'staging/factory_test',
    resourceName: 'factory_test',
    includeAnimations: true,
  });

  assert.equal(calls.modelCompile, 1);
  assert.equal(calls.animationCompile, 1);
  assert.equal(preview.plan.sourcePath, 'authoring/factory_test.bbmodel');
  assert.equal(preview.plan.preserveSource, true);
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.deepEqual(preview.artifacts.map(({kind, path}) => ({kind, path})), [
    {kind: 'model', path: 'staging/factory_test/factory_test.geo.json'},
    {kind: 'animation', path: 'staging/factory_test/factory_test.animation.json'},
  ]);
  assert.deepEqual(preview.artifacts[0].document, geoDocument());
  assert.deepEqual(preview.artifacts[1].document, animationDocument());
});

test('validated preview documents are deeply immutable before trusted staging', () => {
  const {bb} = blockbenchMock();
  const preview = integration.createBlockbenchGeckoLib4Adapter(bb).previewExport({
    profileId: 'geckolib4_entity',
    outputDirectory: 'staging/factory_test',
    resourceName: 'factory_test',
    includeAnimations: true,
  });

  const geo = preview.artifacts[0].document;
  const animation = preview.artifacts[1].document;
  assert.equal(Object.isFrozen(geo), true);
  assert.equal(Object.isFrozen(geo['minecraft:geometry']), true);
  assert.equal(Object.isFrozen(geo['minecraft:geometry'][0]), true);
  assert.equal(Object.isFrozen(geo['minecraft:geometry'][0].bones), true);
  assert.equal(Object.isFrozen(geo['minecraft:geometry'][0].bones[0]), true);
  assert.equal(Object.isFrozen(animation), true);
  assert.equal(Object.isFrozen(animation.animations), true);
  assert.equal(Object.isFrozen(animation.animations['animation.factory_test.idle']), true);
  assert.throws(() => {
    geo['minecraft:geometry'][0].bones[0].name = 'tampered';
  }, TypeError);
  assert.throws(() => {
    animation.animations['animation.factory_test.idle'].loop = false;
  }, TypeError);
});

test('preview can omit animation output and never invokes Animator.buildFile in that mode', () => {
  const {bb, calls} = blockbenchMock();
  const preview = integration.createBlockbenchGeckoLib4Adapter(bb).previewExport({
    profileId: 'geckolib4_block_entity',
    outputDirectory: 'staging/factory_test',
    resourceName: 'factory_test',
    includeAnimations: false,
  });
  assert.equal(calls.modelCompile, 1);
  assert.equal(calls.animationCompile, 0);
  assert.equal(preview.artifacts.length, 1);
  assert.equal(preview.artifacts[0].kind, 'model');
});

test('staging writes only provider artifacts from a validated preview and never overwrites source bbmodel', () => {
  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchGeckoLib4Adapter(bb);
  const preview = adapter.previewExport({
    profileId: 'geckolib4_item',
    outputDirectory: 'staging/factory_test',
    resourceName: 'factory_test',
    includeAnimations: true,
  });
  const writes = [];
  const result = adapter.stageExport(preview, {
    writeText(path, content) { writes.push({path, content}); },
  });

  assert.deepEqual(writes.map((entry) => entry.path), [
    'staging/factory_test/factory_test.geo.json',
    'staging/factory_test/factory_test.animation.json',
  ]);
  assert.equal(writes.some((entry) => entry.path.endsWith('.bbmodel')), false);
  assert.deepEqual(JSON.parse(writes[0].content), geoDocument());
  assert.deepEqual(JSON.parse(writes[1].content), animationDocument());
  assert.deepEqual(result, {
    ok: true,
    staged: 2,
    sourcePath: 'authoring/factory_test.bbmodel',
    preserveSource: true,
    runtimeEvidence: 'UNPROVEN',
  });
});

test('staging rejects untrusted previews and incomplete writer capabilities', () => {
  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchGeckoLib4Adapter(bb);
  assert.throws(
    () => adapter.stageExport({artifacts: []}, {writeText() {}}),
    (error) => error?.code === 'INVALID_GECKOLIB4_EXPORT_PREVIEW',
  );
  const preview = adapter.previewExport({
    profileId: 'geckolib4_armor',
    outputDirectory: 'staging/factory_test',
    resourceName: 'factory_test',
    includeAnimations: false,
  });
  assert.throws(
    () => adapter.stageExport(preview, {}),
    (error) => error?.code === 'INVALID_GECKOLIB4_EXPORT_WRITER',
  );
});

test('malformed compiled provider data is rejected before staging', () => {
  const {bb} = blockbenchMock();
  bb.Codecs.bedrock.compile = () => JSON.stringify({format_version: '1.21.20', 'minecraft:geometry': []});
  const adapter = integration.createBlockbenchGeckoLib4Adapter(bb);
  assert.throws(
    () => adapter.previewExport({
      profileId: 'geckolib4_entity',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'UNSUPPORTED_GECKOLIB4_GEO_FORMAT',
  );
});
