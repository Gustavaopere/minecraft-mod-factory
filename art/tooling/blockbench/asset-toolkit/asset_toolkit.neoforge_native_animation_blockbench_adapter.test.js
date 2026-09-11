'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const adapterPath = path.join(__dirname, 'blockbench-plugin', 'neoforge_native_animation_adapter.js');
const adapterExists = fs.existsSync(adapterPath);

function keyframe(time, interpolation, value) {
  return {
    time,
    interpolation,
    get(axis) {
      return value[{x: 0, y: 1, z: 2}[axis]];
    },
  };
}

function blockbenchMock(overrides = {}) {
  class BoneAnimator {
    constructor(uuid, name) {
      this.uuid = uuid;
      this.name = name;
      this.position = [];
      this.rotation = [
        keyframe(0, 'linear', [0, 0, 0]),
        keyframe(0.5, 'catmullrom', [22.5, 0, 0]),
      ];
      this.scale = [];
    }
  }

  const animator = new BoneAnimator('bone-head', 'head');
  const animation = {
    uuid: 'anim-idle',
    name: 'animation.factory.idle',
    length: 1.125,
    loop: 'loop',
    animators: {head: animator},
    markers: [],
  };
  const project = {
    save_path: 'authoring/factory_test.bbmodel',
    animations: [animation],
  };
  const bb = {
    Blockbench: {isWeb: false, Project: project},
    Animation: {all: project.animations},
    BoneAnimator,
  };
  Object.assign(bb, overrides);
  return {bb, animation};
}

test('PR8 materializes the NeoForge native Blockbench adapter module', () => {
  assert.equal(adapterExists, true, 'blockbench-plugin/neoforge_native_animation_adapter.js must exist before behavioral tests can run');
});

if (adapterExists) {
  const integration = require(adapterPath);

  test('PR8 Blockbench adapter requires desktop authoring with a saved bbmodel source', () => {
    const {bb} = blockbenchMock();
    const adapter = integration.createBlockbenchNeoForgeNativeAnimationAdapter(bb);
    assert.equal(adapter.sourcePath(), 'authoring/factory_test.bbmodel');

    bb.Blockbench.Project.save_path = '';
    assert.throws(
      () => integration.createBlockbenchNeoForgeNativeAnimationAdapter(bb),
      (error) => error?.code === 'NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED',
    );

    bb.Blockbench.Project.save_path = 'authoring/factory_test.bbmodel';
    bb.Blockbench.isWeb = true;
    assert.throws(
      () => integration.createBlockbenchNeoForgeNativeAnimationAdapter(bb),
      (error) => error?.code === 'NEOFORGE_NATIVE_ANIMATION_DESKTOP_REQUIRED',
    );
  });

  test('PR8 preview extracts only audited bone transform channels and writes nothing', () => {
    const {bb} = blockbenchMock();
    const adapter = integration.createBlockbenchNeoForgeNativeAnimationAdapter(bb);
    const preview = adapter.previewExport({
      profileId: 'neoforge_native_entity_animation',
      namespace: 'factory',
      resourceName: 'idle',
      animationId: 'anim-idle',
    });

    assert.deepEqual(preview.plan, {
      profileId: 'neoforge_native_entity_animation',
      sourcePath: 'authoring/factory_test.bbmodel',
      preserveSource: true,
      namespace: 'factory',
      resourceName: 'idle',
      outputPath: 'assets/factory/neoforge/animations/entity/idle.json',
      runtimeEvidence: 'UNPROVEN',
    });
    assert.equal(preview.runtimeEvidence, 'UNPROVEN');
    assert.deepEqual(preview.artifacts.map(({kind, path: outputPath}) => ({kind, path: outputPath})), [
      {kind: 'animation', path: 'assets/factory/neoforge/animations/entity/idle.json'},
    ]);
    assert.deepEqual(preview.artifacts[0].document, {
      length: 1.125,
      loop: true,
      animations: [{
        bone: 'head',
        target: 'minecraft:rotation',
        keyframes: [
          {timestamp: 0, target: [0, 0, 0], interpolation: 'minecraft:linear'},
          {timestamp: 0.5, target: [22.5, 0, 0], interpolation: 'minecraft:catmullrom'},
        ],
      }],
    });
  });

  test('PR8 preview and documents are deeply immutable before trusted staging', () => {
    const {bb} = blockbenchMock();
    const preview = integration.createBlockbenchNeoForgeNativeAnimationAdapter(bb).previewExport({
      profileId: 'neoforge_native_entity_animation',
      namespace: 'factory',
      resourceName: 'idle',
      animationId: 'anim-idle',
    });
    assert.equal(Object.isFrozen(preview), true);
    assert.equal(Object.isFrozen(preview.plan), true);
    assert.equal(Object.isFrozen(preview.artifacts), true);
    assert.equal(Object.isFrozen(preview.artifacts[0].document), true);
    assert.equal(Object.isFrozen(preview.artifacts[0].document.animations[0].keyframes[0]), true);
    assert.throws(() => {
      preview.artifacts[0].document.animations[0].bone = 'tampered';
    }, TypeError);
  });

  test('PR8 staging writes one canonical runtime JSON and never overwrites the bbmodel source', () => {
    const {bb} = blockbenchMock();
    const adapter = integration.createBlockbenchNeoForgeNativeAnimationAdapter(bb);
    const preview = adapter.previewExport({
      profileId: 'neoforge_native_entity_animation',
      namespace: 'factory',
      resourceName: 'idle',
      animationId: 'anim-idle',
    });
    const writes = [];
    const result = adapter.stageExport(preview, {
      writeText(outputPath, content) { writes.push({path: outputPath, content}); },
    });
    assert.deepEqual(writes.map((entry) => entry.path), ['assets/factory/neoforge/animations/entity/idle.json']);
    assert.equal(writes.some((entry) => entry.path.endsWith('.bbmodel')), false);
    assert.deepEqual(JSON.parse(writes[0].content), preview.artifacts[0].document);
    assert.equal(writes[0].content.endsWith('\n'), true);
    assert.deepEqual(result, {
      ok: true,
      staged: 1,
      sourcePath: 'authoring/factory_test.bbmodel',
      preserveSource: true,
      runtimeEvidence: 'UNPROVEN',
    });
  });

  test('PR8 staging rejects forged previews and incomplete writers', () => {
    const {bb} = blockbenchMock();
    const adapter = integration.createBlockbenchNeoForgeNativeAnimationAdapter(bb);
    assert.throws(
      () => adapter.stageExport({artifacts: []}, {writeText() {}}),
      (error) => error?.code === 'INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_PREVIEW',
    );
    const preview = adapter.previewExport({
      profileId: 'neoforge_native_entity_animation',
      namespace: 'factory',
      resourceName: 'idle',
      animationId: 'anim-idle',
    });
    assert.throws(
      () => adapter.stageExport(preview, {}),
      (error) => error?.code === 'INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_WRITER',
    );
  });

  test('PR8 preview fails closed on missing animation, unsupported loop/easing, effect markers and non-bone animators', () => {
    const missing = blockbenchMock();
    const missingAdapter = integration.createBlockbenchNeoForgeNativeAnimationAdapter(missing.bb);
    assert.throws(
      () => missingAdapter.previewExport({profileId: 'neoforge_native_entity_animation', namespace: 'factory', resourceName: 'idle', animationId: 'missing'}),
      (error) => error?.code === 'NEOFORGE_NATIVE_ANIMATION_NOT_FOUND',
    );

    const hold = blockbenchMock();
    hold.animation.loop = 'hold';
    assert.throws(
      () => integration.createBlockbenchNeoForgeNativeAnimationAdapter(hold.bb).previewExport({profileId: 'neoforge_native_entity_animation', namespace: 'factory', resourceName: 'idle', animationId: 'anim-idle'}),
      (error) => error?.code === 'UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_LOOP_MODE',
    );

    const bezier = blockbenchMock();
    bezier.animation.animators.head.rotation[0].interpolation = 'bezier';
    assert.throws(
      () => integration.createBlockbenchNeoForgeNativeAnimationAdapter(bezier.bb).previewExport({profileId: 'neoforge_native_entity_animation', namespace: 'factory', resourceName: 'idle', animationId: 'anim-idle'}),
      (error) => error?.code === 'UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_INTERPOLATION',
    );

    const marker = blockbenchMock();
    marker.animation.markers.push({time: 0.25, name: 'sound'});
    assert.throws(
      () => integration.createBlockbenchNeoForgeNativeAnimationAdapter(marker.bb).previewExport({profileId: 'neoforge_native_entity_animation', namespace: 'factory', resourceName: 'idle', animationId: 'anim-idle'}),
      (error) => error?.code === 'UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_EFFECT_MARKERS',
    );

    const other = blockbenchMock();
    other.animation.animators.extra = {name: 'not-a-bone', rotation: []};
    assert.throws(
      () => integration.createBlockbenchNeoForgeNativeAnimationAdapter(other.bb).previewExport({profileId: 'neoforge_native_entity_animation', namespace: 'factory', resourceName: 'idle', animationId: 'anim-idle'}),
      (error) => error?.code === 'UNPROVEN_NEOFORGE_NATIVE_ANIMATION_ANIMATOR',
    );
  });
}
