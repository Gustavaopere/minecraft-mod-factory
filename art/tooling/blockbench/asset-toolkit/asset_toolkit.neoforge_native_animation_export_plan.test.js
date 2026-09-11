'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');

function planner() {
  assert.equal(typeof core.createNeoForgeNativeAnimationExportPlan, 'function', 'missing core.createNeoForgeNativeAnimationExportPlan');
  return core.createNeoForgeNativeAnimationExportPlan;
}

test('PR8 export plan preserves the bbmodel source and derives the exact NeoForge runtime resource path', () => {
  const createPlan = planner();
  assert.deepEqual(createPlan({
    profileId: 'neoforge_native_entity_animation',
    sourcePath: 'authoring/factory_test.bbmodel',
    namespace: 'factory',
    resourceName: 'entity/idle',
  }), {
    profileId: 'neoforge_native_entity_animation',
    sourcePath: 'authoring/factory_test.bbmodel',
    preserveSource: true,
    namespace: 'factory',
    resourceName: 'entity/idle',
    outputPath: 'assets/factory/neoforge/animations/entity/entity/idle.json',
    runtimeEvidence: 'UNPROVEN',
  });
});

test('PR8 export plan permits absolute authoring authority paths but never absolute or escaping runtime outputs', () => {
  const createPlan = planner();
  const linux = createPlan({
    profileId: 'neoforge_native_entity_animation',
    sourcePath: '/home/gustavo/factory_test.bbmodel',
    namespace: 'factory',
    resourceName: 'idle',
  });
  assert.equal(linux.sourcePath, '/home/gustavo/factory_test.bbmodel');
  assert.equal(linux.outputPath, 'assets/factory/neoforge/animations/entity/idle.json');

  const windows = createPlan({
    profileId: 'neoforge_native_entity_animation',
    sourcePath: 'C:\\Users\\Gustavo\\factory_test.bbmodel',
    namespace: 'factory',
    resourceName: 'idle',
  });
  assert.equal(windows.sourcePath, 'C:/Users/Gustavo/factory_test.bbmodel');

  for (const resourceName of ['/idle', '../idle', 'entity/../idle', 'Idle', 'idle.json']) {
    assert.throws(
      () => createPlan({
        profileId: 'neoforge_native_entity_animation',
        sourcePath: 'authoring/factory_test.bbmodel',
        namespace: 'factory',
        resourceName,
      }),
      (error) => error?.code === 'INVALID_NEOFORGE_NATIVE_ANIMATION_PATH',
      resourceName,
    );
  }
});

test('PR8 export plan rejects wrong profiles, unsaved/non-bbmodel sources and invalid namespaces', () => {
  const createPlan = planner();
  assert.throws(
    () => createPlan({profileId: 'geckolib4_entity', sourcePath: 'factory.bbmodel', namespace: 'factory', resourceName: 'idle'}),
    (error) => error?.code === 'NEOFORGE_NATIVE_ANIMATION_PROFILE_REQUIRED',
  );
  for (const sourcePath of ['', 'factory.json']) {
    assert.throws(
      () => createPlan({profileId: 'neoforge_native_entity_animation', sourcePath, namespace: 'factory', resourceName: 'idle'}),
      (error) => error?.code === 'NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED',
    );
  }
  for (const namespace of ['', 'Factory', 'factory/path']) {
    assert.throws(
      () => createPlan({profileId: 'neoforge_native_entity_animation', sourcePath: 'factory.bbmodel', namespace, resourceName: 'idle'}),
      (error) => error?.code === 'INVALID_NEOFORGE_NATIVE_ANIMATION_NAMESPACE',
    );
  }
});
