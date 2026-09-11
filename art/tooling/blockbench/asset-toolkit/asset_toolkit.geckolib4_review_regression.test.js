'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const integration = require('./blockbench-plugin/geckolib4_adapter.js');

function blockbenchMock() {
  return {
    Blockbench: {
      isWeb: false,
      Project: {
        format: {id: 'geckolib_model'},
        save_path: '/home/gustavo/minecraft/factory_test.bbmodel',
      },
    },
    Codecs: {
      bedrock: {
        compile() {
          return {
            format_version: '1.12.0',
            'minecraft:geometry': [{
              description: {identifier: 'geometry.factory_test', texture_width: 16, texture_height: 16},
              bones: [{name: 'root', pivot: [0, 0, 0]}],
            }],
          };
        },
      },
    },
    Animator: {
      buildFile() {
        return {
          format_version: '1.8.0',
          animations: {'animation.factory_test.idle': {bones: {root: {rotation: [0, 0, 0]}}}},
        };
      },
    },
  };
}

test('Windows drive-absolute output directories fail closed while absolute source authority remains valid', () => {
  const adapter = integration.createBlockbenchGeckoLib4Adapter(blockbenchMock());
  assert.throws(
    () => adapter.previewExport({
      profileId: 'geckolib4_entity',
      outputDirectory: 'C:\\Users\\Gustavo\\staging',
      resourceName: 'factory_test',
      includeAnimations: false,
    }),
    (error) => error?.code === 'INVALID_GECKOLIB4_PATH',
  );
});

test('validated preview documents are deeply immutable before staging', () => {
  const adapter = integration.createBlockbenchGeckoLib4Adapter(blockbenchMock());
  const preview = adapter.previewExport({
    profileId: 'geckolib4_entity',
    outputDirectory: 'staging/factory_test',
    resourceName: 'factory_test',
    includeAnimations: false,
  });
  const document = preview.artifacts[0].document;
  const geometry = document['minecraft:geometry'];
  const bone = geometry[0].bones[0];
  assert.equal(Object.isFrozen(document), true);
  assert.equal(Object.isFrozen(geometry), true);
  assert.equal(Object.isFrozen(geometry[0]), true);
  assert.equal(Object.isFrozen(bone), true);
  assert.equal(Object.isFrozen(bone.pivot), true);
  assert.throws(() => { bone.pivot[0] = 99; }, TypeError);
  assert.equal(bone.pivot[0], 0);
});
