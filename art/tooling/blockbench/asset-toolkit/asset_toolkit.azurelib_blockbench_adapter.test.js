'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const integration = require('./blockbench-plugin/azurelib_adapter.js');

function geoDocument() {
  return {
    format_version: '1.12.0',
    'minecraft:geometry': [{
      description: {identifier: 'geometry.factory_azure_test', texture_width: 16, texture_height: 16},
      bones: [{name: 'root', pivot: [0, 0, 0], locators: {muzzle: [1, 2, 3]}}],
    }],
  };
}

function animationDocument() {
  return {
    format_version: '1.8.0',
    includes: [{file_id: 'factory:animations/shared.animation.json', animations: ['animation.factory.shared']}],
    animations: {
      'animation.factory_azure_test.idle': {
        animation_length: 2,
        loop: true,
        bones: {
          root: {
            rotation: {
              '0': [0, 0, 0],
              '0.125': {vector: [0, 5, 0], easing: 'easeInSine'},
              '0.25': {vector: [0, 10, 0]},
              '1': {vector: [0, 15, 0]},
              '2': {vector: [0, 20, 0]},
            },
          },
        },
        particle_effects: {'0.5': {effect: 'factory:test_particle', locator: 'muzzle'}},
      },
    },
  };
}

function orderedAnimationText() {
  return [
    '{',
    '  "format_version": "1.8.0",',
    '  "animations": {',
    '    "animation.factory_azure_test.idle": {',
    '      "animation_length": 2,',
    '      "loop": true,',
    '      "bones": {',
    '        "root": {',
    '          "rotation": {',
    '            "0": [0, 0, 0],',
    '            "0.125": {"vector": [0, 5, 0], "easing": "easeInSine"},',
    '            "0.25": {"vector": [0, 10, 0]},',
    '            "1": {"vector": [0, 15, 0]},',
    '            "2": {"vector": [0, 20, 0]}',
    '          }',
    '        }',
    '      },',
    '      "particle_effects": {"0.5": {"effect": "factory:test_particle", "locator": "muzzle"}}',
    '    }',
    '  },',
    '  "includes": [{"file_id": "factory:animations/shared.animation.json", "animations": ["animation.factory.shared"]}]',
    '}',
  ].join('\n');
}

function blockbenchMock(overrides = {}) {
  const calls = {
    modelCompile: 0,
    animationCompile: 0,
    animationWrite: 0,
    animatorBuildFile: 0,
  };
  const animationCodec = {
    id: 'azure_animation',
    compileFile() {
      calls.animationCompile++;
      return animationDocument();
    },
    write(content) {
      calls.animationWrite++;
      assert.deepEqual(content, animationDocument());
      return orderedAnimationText();
    },
  };
  const bb = {
    Blockbench: {
      isWeb: false,
      Project: {
        format: {id: 'azure_model', animation_codec: animationCodec},
        save_path: 'authoring/factory_azure_test.bbmodel',
        azureIKChains: [{name: 'authoring_only_leg'}],
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
        calls.animatorBuildFile++;
        throw new Error('AzureLib PR7 must not use GeckoLib Animator.buildFile');
      },
    },
  };
  return {bb: Object.assign(bb, overrides), calls, animationCodec};
}

test('Blockbench AzureLib adapter requires active azure_model source saved as native bbmodel', () => {
  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchAzureLibAdapter(bb);
  assert.equal(adapter.sourcePath(), 'authoring/factory_azure_test.bbmodel');

  bb.Blockbench.Project.format.id = 'geckolib_model';
  assert.throws(
    () => integration.createBlockbenchAzureLibAdapter(bb),
    (error) => error?.code === 'AZURELIB_PROJECT_FORMAT_REQUIRED',
  );

  bb.Blockbench.Project.format.id = 'azure_model';
  bb.Blockbench.Project.save_path = '';
  assert.throws(
    () => integration.createBlockbenchAzureLibAdapter(bb),
    (error) => error?.code === 'AZURELIB_SOURCE_NOT_SAVED',
  );
});

test('preview accepts absolute native Blockbench save paths while output staging remains relative', () => {
  for (const [sourcePath, expectedSourcePath] of [
    ['/home/gustavo/minecraft/factory_azure_test.bbmodel', '/home/gustavo/minecraft/factory_azure_test.bbmodel'],
    ['C:\\Users\\Gustavo\\Minecraft\\factory_azure_test.bbmodel', 'C:/Users/Gustavo/Minecraft/factory_azure_test.bbmodel'],
  ]) {
    const {bb} = blockbenchMock();
    bb.Blockbench.Project.save_path = sourcePath;
    const adapter = integration.createBlockbenchAzureLibAdapter(bb);
    assert.equal(adapter.sourcePath(), expectedSourcePath);
    const preview = adapter.previewExport({
      profileId: 'azurelib_entity',
      outputDirectory: 'staging/factory_azure_test',
      resourceName: 'factory_azure_test',
      includeAnimations: false,
    });
    assert.equal(preview.plan.sourcePath, expectedSourcePath);
  }

  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchAzureLibAdapter(bb);
  assert.throws(
    () => adapter.previewExport({
      profileId: 'azurelib_entity',
      outputDirectory: '/absolute/staging',
      resourceName: 'factory_azure_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'INVALID_AZURELIB_PATH',
  );
});

test('preview compiles model through Bedrock codec and animation through Azure AnimationCodec, never Animator.buildFile', () => {
  const {bb, calls} = blockbenchMock();
  const adapter = integration.createBlockbenchAzureLibAdapter(bb);
  const preview = adapter.previewExport({
    profileId: 'azurelib_entity',
    outputDirectory: 'staging/factory_azure_test',
    resourceName: 'factory_azure_test',
    includeAnimations: true,
  });

  assert.equal(calls.modelCompile, 1);
  assert.equal(calls.animationCompile, 1);
  assert.equal(calls.animationWrite, 1);
  assert.equal(calls.animatorBuildFile, 0);
  assert.equal(preview.plan.preserveSource, true);
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.deepEqual(preview.artifacts.map(({kind, path}) => ({kind, path})), [
    {kind: 'model', path: 'staging/factory_azure_test/factory_azure_test.geo.json'},
    {kind: 'animation', path: 'staging/factory_azure_test/factory_azure_test.animation.json'},
  ]);
  assert.deepEqual(preview.artifacts[0].document, geoDocument());
  assert.deepEqual(preview.artifacts[1].document, animationDocument());
  assert.equal(preview.artifacts[1].serializedContent, orderedAnimationText());
});

test('validated AzureLib preview documents are deeply immutable before trusted staging', () => {
  const {bb} = blockbenchMock();
  const preview = integration.createBlockbenchAzureLibAdapter(bb).previewExport({
    profileId: 'azurelib_entity',
    outputDirectory: 'staging/factory_azure_test',
    resourceName: 'factory_azure_test',
    includeAnimations: true,
  });

  const geo = preview.artifacts[0].document;
  const animation = preview.artifacts[1].document;
  assert.equal(Object.isFrozen(geo), true);
  assert.equal(Object.isFrozen(geo['minecraft:geometry']), true);
  assert.equal(Object.isFrozen(geo['minecraft:geometry'][0].bones[0]), true);
  assert.equal(Object.isFrozen(animation), true);
  assert.equal(Object.isFrozen(animation.animations), true);
  assert.equal(Object.isFrozen(animation.animations['animation.factory_azure_test.idle']), true);
  assert.throws(() => {
    geo['minecraft:geometry'][0].bones[0].name = 'tampered';
  }, TypeError);
  assert.throws(() => {
    animation.animations['animation.factory_azure_test.idle'].loop = false;
  }, TypeError);
});

test('preview without animations never touches the Azure animation codec or GeckoLib-style Animator path', () => {
  const {bb, calls} = blockbenchMock();
  const preview = integration.createBlockbenchAzureLibAdapter(bb).previewExport({
    profileId: 'azurelib_block',
    outputDirectory: 'staging/factory_azure_test',
    resourceName: 'factory_azure_test',
    includeAnimations: false,
  });
  assert.equal(calls.modelCompile, 1);
  assert.equal(calls.animationCompile, 0);
  assert.equal(calls.animationWrite, 0);
  assert.equal(calls.animatorBuildFile, 0);
  assert.equal(preview.artifacts.length, 1);
  assert.equal(preview.artifacts[0].kind, 'model');
});

test('staging uses the Azure codec serialized animation verbatim so fractional keyframe order is preserved', () => {
  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchAzureLibAdapter(bb);
  const preview = adapter.previewExport({
    profileId: 'azurelib_item',
    outputDirectory: 'staging/factory_azure_test',
    resourceName: 'factory_azure_test',
    includeAnimations: true,
  });
  const writes = [];
  const result = adapter.stageExport(preview, {
    writeText(path, content) { writes.push({path, content}); },
  });

  assert.deepEqual(writes.map((entry) => entry.path), [
    'staging/factory_azure_test/factory_azure_test.geo.json',
    'staging/factory_azure_test/factory_azure_test.animation.json',
  ]);
  assert.equal(writes.some((entry) => entry.path.endsWith('.bbmodel')), false);
  assert.deepEqual(JSON.parse(writes[0].content), geoDocument());

  const animationText = writes[1].content;
  assert.equal(animationText.trim(), orderedAnimationText());
  const positions = ['"0"', '"0.125"', '"0.25"', '"1"', '"2"'].map((key) => animationText.indexOf(key));
  assert.ok(positions.every((position) => position >= 0), positions.join(','));
  assert.deepEqual([...positions].sort((left, right) => left - right), positions, 'fractional timestamps must remain chronological');
  assert.equal(animationText.includes('azureIKChains'), false, 'authoring-only FABRIK metadata must not leak into runtime artifacts');

  assert.deepEqual(result, {
    ok: true,
    staged: 2,
    sourcePath: 'authoring/factory_azure_test.bbmodel',
    preserveSource: true,
    runtimeEvidence: 'UNPROVEN',
  });
});

test('Blockbench adapter fails closed when Azure AnimationCodec compile/write APIs are unavailable', () => {
  const {bb} = blockbenchMock();
  bb.Blockbench.Project.format.animation_codec = {id: 'azure_animation'};
  const adapter = integration.createBlockbenchAzureLibAdapter(bb);
  assert.throws(
    () => adapter.previewExport({
      profileId: 'azurelib_armor',
      outputDirectory: 'staging/factory_azure_test',
      resourceName: 'factory_azure_test',
      includeAnimations: true,
    }),
    (error) => error?.code === 'AZURELIB_ANIMATION_CODEC_UNAVAILABLE',
  );
});

test('staging rejects untrusted previews and incomplete writer capabilities', () => {
  const {bb} = blockbenchMock();
  const adapter = integration.createBlockbenchAzureLibAdapter(bb);
  assert.throws(
    () => adapter.stageExport({artifacts: []}, {writeText() {}}),
    (error) => error?.code === 'INVALID_AZURELIB_EXPORT_PREVIEW',
  );
  const preview = adapter.previewExport({
    profileId: 'azurelib_armor',
    outputDirectory: 'staging/factory_azure_test',
    resourceName: 'factory_azure_test',
    includeAnimations: false,
  });
  assert.throws(
    () => adapter.stageExport(preview, {}),
    (error) => error?.code === 'INVALID_AZURELIB_EXPORT_WRITER',
  );
});

test('malformed compiled provider data is rejected before staging', () => {
  const {bb} = blockbenchMock();
  bb.Codecs.bedrock.compile = () => JSON.stringify({format_version: '1.21.20', 'minecraft:geometry': []});
  const adapter = integration.createBlockbenchAzureLibAdapter(bb);
  assert.throws(
    () => adapter.previewExport({
      profileId: 'azurelib_entity',
      outputDirectory: 'staging/factory_azure_test',
      resourceName: 'factory_azure_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'UNSUPPORTED_AZURELIB_GEO_FORMAT',
  );
});
