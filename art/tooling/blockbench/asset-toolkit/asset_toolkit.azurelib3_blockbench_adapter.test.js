'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const adapterPath = path.join(__dirname, 'blockbench-plugin', 'azurelib3_adapter.js');
const adapterExists = fs.existsSync(adapterPath);

function geoDocument(formatVersion = '1.21.0') {
  return {
    format_version: formatVersion,
    'minecraft:geometry': [{
      description: {identifier: 'geometry.factory_test', texture_width: 16, texture_height: 16},
      bones: [{name: 'root', pivot: [0, 0, 0], cubes: [], locators: {muzzle: [1, 2, 3]}}],
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
        bones: {
          root: {
            rotation: {vector: [0, 0, 0], easing: 'easeInOutSine'},
          },
        },
        sound_effects: {'0.25': {effect: 'factory:test_sound'}},
      },
    },
  };
}

function blockbenchMock(overrides = {}) {
  const calls = {
    modelCompile: 0,
    animationCompile: 0,
    animationWrite: 0,
    animationWritePath: null,
  };
  const animationCodec = {
    compileFile() {
      calls.animationCompile++;
      return animationDocument();
    },
    write(content, outputPath) {
      calls.animationWrite++;
      calls.animationWritePath = outputPath;
      return `${JSON.stringify(content, null, 4)}\n`;
    },
  };
  const format = {id: 'azure_model', animation_codec: animationCodec};
  const bb = {
    Blockbench: {
      isWeb: false,
      Project: {
        format,
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
  };
  return {bb: Object.assign(bb, overrides), calls, animationCodec};
}

test('PR7 materializes the AzureLib 3 Blockbench provider adapter module', () => {
  assert.equal(adapterExists, true, 'blockbench-plugin/azurelib3_adapter.js must exist before behavioral tests can run');
});

if (adapterExists) {
  const integration = require(adapterPath);

  test('Blockbench AzureLib adapter requires desktop azure_model authoring with a saved bbmodel source', () => {
    const {bb} = blockbenchMock();
    const adapter = integration.createBlockbenchAzureLib3Adapter(bb);
    assert.equal(adapter.sourcePath(), 'authoring/factory_test.bbmodel');

    bb.Blockbench.Project.format.id = 'java_block';
    assert.throws(
      () => integration.createBlockbenchAzureLib3Adapter(bb),
      (error) => error?.code === 'AZURELIB3_PROJECT_FORMAT_REQUIRED',
    );

    bb.Blockbench.Project.format.id = 'azure_model';
    bb.Blockbench.Project.save_path = '';
    assert.throws(
      () => integration.createBlockbenchAzureLib3Adapter(bb),
      (error) => error?.code === 'AZURELIB3_SOURCE_NOT_SAVED',
    );

    bb.Blockbench.Project.save_path = 'authoring/factory_test.bbmodel';
    bb.Blockbench.isWeb = true;
    assert.throws(
      () => integration.createBlockbenchAzureLib3Adapter(bb),
      (error) => error?.code === 'AZURELIB3_DESKTOP_REQUIRED',
    );
  });

  test('preview accepts absolute source-authority paths while output staging remains relative', () => {
    for (const [sourcePath, expectedSourcePath] of [
      ['/home/gustavo/minecraft/factory_test.bbmodel', '/home/gustavo/minecraft/factory_test.bbmodel'],
      ['C:\\Users\\Gustavo\\Minecraft\\factory_test.bbmodel', 'C:/Users/Gustavo/Minecraft/factory_test.bbmodel'],
    ]) {
      const {bb} = blockbenchMock();
      bb.Blockbench.Project.save_path = sourcePath;
      const adapter = integration.createBlockbenchAzureLib3Adapter(bb);
      assert.equal(adapter.sourcePath(), expectedSourcePath);
      const preview = adapter.previewExport({
        profileId: 'azurelib_entity',
        outputDirectory: 'staging/factory_test',
        resourceName: 'factory_test',
        includeAnimations: false,
      });
      assert.equal(preview.plan.sourcePath, expectedSourcePath);
    }

    const {bb} = blockbenchMock();
    const adapter = integration.createBlockbenchAzureLib3Adapter(bb);
    assert.throws(
      () => adapter.previewExport({
        profileId: 'azurelib_entity',
        outputDirectory: '/absolute/staging',
        resourceName: 'factory_test',
        includeAnimations: false,
      }),
      (error) => error?.code === 'INVALID_AZURELIB3_PATH',
    );
  });

  test('preview compiles model through Codecs.bedrock and animation through the active AzureLib animation codec without writing', () => {
    const {bb, calls} = blockbenchMock();
    const adapter = integration.createBlockbenchAzureLib3Adapter(bb);
    const preview = adapter.previewExport({
      profileId: 'azurelib_entity',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    });

    assert.equal(calls.modelCompile, 1);
    assert.equal(calls.animationCompile, 1);
    assert.equal(calls.animationWrite, 0);
    assert.equal(preview.plan.sourcePath, 'authoring/factory_test.bbmodel');
    assert.equal(preview.plan.preserveSource, true);
    assert.equal(preview.runtimeEvidence, 'UNPROVEN');
    assert.deepEqual(preview.artifacts.map(({kind, path: outputPath}) => ({kind, path: outputPath})), [
      {kind: 'model', path: 'staging/factory_test/factory_test.geo.json'},
      {kind: 'animation', path: 'staging/factory_test/factory_test.animation.json'},
    ]);
    assert.deepEqual(preview.artifacts[0].document, geoDocument());
    assert.deepEqual(preview.artifacts[1].document, animationDocument());
  });

  test('validated preview documents are deeply immutable before trusted staging', () => {
    const {bb} = blockbenchMock();
    const preview = integration.createBlockbenchAzureLib3Adapter(bb).previewExport({
      profileId: 'azurelib_entity',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    });

    const geo = preview.artifacts[0].document;
    const animation = preview.artifacts[1].document;
    assert.equal(Object.isFrozen(geo), true);
    assert.equal(Object.isFrozen(geo['minecraft:geometry']), true);
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

  test('preview can omit animation output and never invokes the provider animation codec in that mode', () => {
    const {bb, calls} = blockbenchMock();
    const preview = integration.createBlockbenchAzureLib3Adapter(bb).previewExport({
      profileId: 'azurelib_block',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: false,
    });
    assert.equal(calls.modelCompile, 1);
    assert.equal(calls.animationCompile, 0);
    assert.equal(calls.animationWrite, 0);
    assert.equal(preview.artifacts.length, 1);
    assert.equal(preview.artifacts[0].kind, 'model');
  });

  test('staging uses the AzureLib animation codec write serializer and never overwrites the bbmodel source', () => {
    const {bb, calls} = blockbenchMock();
    const adapter = integration.createBlockbenchAzureLib3Adapter(bb);
    const preview = adapter.previewExport({
      profileId: 'azurelib_item',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    });
    const writes = [];
    const result = adapter.stageExport(preview, {
      writeText(outputPath, content) { writes.push({path: outputPath, content}); },
    });

    assert.deepEqual(writes.map((entry) => entry.path), [
      'staging/factory_test/factory_test.geo.json',
      'staging/factory_test/factory_test.animation.json',
    ]);
    assert.equal(writes.some((entry) => entry.path.endsWith('.bbmodel')), false);
    assert.deepEqual(JSON.parse(writes[0].content), geoDocument());
    assert.equal(writes[1].content, `${JSON.stringify(animationDocument(), null, 4)}\n`);
    assert.equal(calls.animationWrite, 1);
    assert.equal(calls.animationWritePath, 'staging/factory_test/factory_test.animation.json');
    assert.deepEqual(result, {
      ok: true,
      staged: 2,
      sourcePath: 'authoring/factory_test.bbmodel',
      preserveSource: true,
      runtimeEvidence: 'UNPROVEN',
    });
  });

  test('staging rejects untrusted previews, incomplete writers and invalid animation serializer output', () => {
    const {bb, animationCodec} = blockbenchMock();
    const adapter = integration.createBlockbenchAzureLib3Adapter(bb);
    assert.throws(
      () => adapter.stageExport({artifacts: []}, {writeText() {}}),
      (error) => error?.code === 'INVALID_AZURELIB3_EXPORT_PREVIEW',
    );
    const preview = adapter.previewExport({
      profileId: 'azurelib_armor',
      outputDirectory: 'staging/factory_test',
      resourceName: 'factory_test',
      includeAnimations: true,
    });
    assert.throws(
      () => adapter.stageExport(preview, {}),
      (error) => error?.code === 'INVALID_AZURELIB3_EXPORT_WRITER',
    );

    animationCodec.write = () => ({not: 'text'});
    assert.throws(
      () => adapter.stageExport(preview, {writeText() {}}),
      (error) => error?.code === 'INVALID_AZURELIB3_ANIMATION_SERIALIZATION',
    );
  });

  test('missing provider hooks and malformed provider documents fail closed before staging', () => {
    const noModel = blockbenchMock();
    delete noModel.bb.Codecs.bedrock.compile;
    assert.throws(
      () => integration.createBlockbenchAzureLib3Adapter(noModel.bb),
      (error) => error?.code === 'AZURELIB3_MODEL_CODEC_UNAVAILABLE',
    );

    const noAnimation = blockbenchMock();
    delete noAnimation.bb.Blockbench.Project.format.animation_codec.write;
    assert.throws(
      () => integration.createBlockbenchAzureLib3Adapter(noAnimation.bb).previewExport({
        profileId: 'azurelib_entity',
        outputDirectory: 'staging/factory_test',
        resourceName: 'factory_test',
        includeAnimations: true,
      }),
      (error) => error?.code === 'AZURELIB3_ANIMATION_CODEC_UNAVAILABLE',
    );

    const invalidGeo = blockbenchMock();
    invalidGeo.bb.Codecs.bedrock.compile = () => JSON.stringify(geoDocument('1.21.20'));
    assert.throws(
      () => integration.createBlockbenchAzureLib3Adapter(invalidGeo.bb).previewExport({
        profileId: 'azurelib_entity',
        outputDirectory: 'staging/factory_test',
        resourceName: 'factory_test',
        includeAnimations: false,
      }),
      (error) => error?.code === 'UNSUPPORTED_AZURELIB3_GEO_FORMAT',
    );

    const invalidAnimation = blockbenchMock();
    invalidAnimation.bb.Blockbench.Project.format.animation_codec.compileFile = () => {
      const document = animationDocument();
      document.animations['animation.factory_test.idle'].bones.root.rotation.easing = 'unknownCurve';
      return document;
    };
    assert.throws(
      () => integration.createBlockbenchAzureLib3Adapter(invalidAnimation.bb).previewExport({
        profileId: 'azurelib_entity',
        outputDirectory: 'staging/factory_test',
        resourceName: 'factory_test',
        includeAnimations: true,
      }),
      (error) => error?.code === 'UNSUPPORTED_AZURELIB3_EASING',
    );
  });
}
