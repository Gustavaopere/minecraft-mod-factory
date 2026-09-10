'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  applyAnimationBatch,
  playPreview,
  stopPreview,
  inspectPose,
  capturePose,
} = require('./core/animation/animation_engine.js');
const {createBlockbenchAnimationAdapter} = require('./blockbench-plugin/animation_adapter.js');

function mockBlockbench() {
  let serial = 0;
  const events = [];
  const project = {
    name: 'animation_asset',
    save_path: '/tmp/animation_asset.bbmodel',
    format: {id: 'free'},
    groups: [],
    elements: [],
    textures: [],
    animations: [],
    selected_elements: [],
  };

  class Group {
    static all = project.groups;
    constructor(name, uuid) {
      this.name = name;
      this.uuid = uuid;
      this.origin = [0, 0, 0];
      this.parent = null;
      this.mesh = {
        position: {x: 0, y: 0, z: 0},
        rotation: {x: 0, y: 0, z: 0},
        scale: {x: 1, y: 1, z: 1},
      };
      project.groups.push(this);
    }
  }

  class BoneAnimator {
    constructor(uuid, animation) {
      this.uuid = uuid;
      this.animation = animation;
      this.keyframes = [];
      this.position = [];
      this.rotation = [];
      this.scale = [];
    }
    addKeyframe(data, uuid) {
      const point = data.data_points?.[0] || {};
      const keyframe = {
        uuid: uuid || `keyframe-${++serial}`,
        channel: data.channel,
        time: data.time,
        interpolation: data.interpolation,
        data_points: [{x: point.x, y: point.y, z: point.z}],
        animator: this,
        extend: (update) => {
          if (update.channel !== undefined) keyframe.channel = update.channel;
          if (update.time !== undefined) keyframe.time = update.time;
          if (update.interpolation !== undefined) keyframe.interpolation = update.interpolation;
          if (update.data_points?.[0]) {
            const next = update.data_points[0];
            keyframe.data_points[0] = {x: next.x, y: next.y, z: next.z};
          }
          return keyframe;
        },
        remove: () => {
          this.keyframes = this.keyframes.filter((entry) => entry !== keyframe);
          for (const channel of ['position', 'rotation', 'scale']) {
            this[channel] = this[channel].filter((entry) => entry !== keyframe);
          }
        },
      };
      this.keyframes.push(keyframe);
      this[data.channel].push(keyframe);
      return keyframe;
    }
  }

  class Animation {
    static all = project.animations;
    static selected = null;
    constructor(data = {}) {
      this.uuid = data.uuid || `animation-${++serial}`;
      this.name = data.name || 'animation.unnamed';
      this.length = data.length ?? 1;
      this.loop = data.loop || 'once';
      this.animators = {};
      this.markers = [];
      this.playing = false;
      this.time = 0;
    }
    add() {
      if (!Animation.all.includes(this)) Animation.all.push(this);
      return this;
    }
    remove() {
      const index = Animation.all.indexOf(this);
      if (index >= 0) Animation.all.splice(index, 1);
      if (Animation.selected === this) Animation.selected = null;
      return this;
    }
    setLength(value) { this.length = value; }
    setLoop(value) { this.loop = value; }
    select() { Animation.selected = this; return this; }
    getBoneAnimator(node) {
      if (!node || !node.uuid) return null;
      if (!this.animators[node.uuid]) this.animators[node.uuid] = new BoneAnimator(node.uuid, this);
      return this.animators[node.uuid];
    }
    togglePlayingState(state) { this.playing = Boolean(state); return this.playing; }
  }

  const root = new Group('root', 'bone-root');
  const hand = new Group('hand', 'bone-hand');
  hand.origin = [0, 8, 0];

  const preview = {
    loadedPresets: [],
    loadAnglePreset(preset) { this.loadedPresets.push(preset.id); },
  };

  const bb = {
    events,
    project,
    root,
    hand,
    Blockbench: {Project: project, isWeb: false, version: '5.1.6'},
    Group,
    Animation,
    Animator: {
      previewCalls: 0,
      preview() {
        this.previewCalls += 1;
        const animation = Animation.selected;
        if (!animation) return;
        root.mesh.position.x = animation.time;
        root.mesh.rotation.y = animation.time * 2;
        root.mesh.scale.z = 1 + animation.time;
      },
      showDefaultPose() {
        root.mesh.position.x = 0;
        root.mesh.rotation.y = 0;
        root.mesh.scale.z = 1;
      },
    },
    Undo: {
      initEdit(aspects) { events.push(['undo.begin', aspects]); },
      finishEdit(label, aspects) { events.push(['undo.finish', label, aspects]); },
      cancelEdit(revert) { events.push(['undo.cancel', revert]); },
    },
    Preview: {selected: preview},
    DefaultCameraPresets: [
      {id: 'front', name: 'Front'},
      {id: 'isometric_right', name: 'Isometric Right'},
    ],
    Screencam: {
      screenshotPreview(target, options, callback) {
        events.push(['capture', target === preview, options]);
        callback('data:image/png;base64,AAAA');
      },
    },
  };
  return bb;
}

function createAnimation(adapter) {
  const before = adapter.getRevision();
  return applyAnimationBatch(adapter, {
    expectedRevision: before,
    operations: [
      {type: 'animation_create', id: 'anim-idle', name: 'animation.example.idle', length: 1, loop: 'loop'},
    ],
  });
}

test('Blockbench animation adapter is desktop-only and fails closed when required animation APIs are absent', () => {
  const web = mockBlockbench();
  web.Blockbench.isWeb = true;
  assert.throws(() => createBlockbenchAnimationAdapter(web), /DESKTOP_REQUIRED/);

  const missingAnimation = mockBlockbench();
  delete missingAnimation.Animation;
  assert.throws(() => createBlockbenchAnimationAdapter(missingAnimation), /BLOCKBENCH_API_UNAVAILABLE/);

  const missingUndo = mockBlockbench();
  delete missingUndo.Undo.finishEdit;
  assert.throws(() => createBlockbenchAnimationAdapter(missingUndo), /BLOCKBENCH_API_UNAVAILABLE/);
});

test('adapter creates animations and keyframes with revision guards and one Undo transaction per batch', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchAnimationAdapter(bb);
  const created = createAnimation(adapter);
  assert.equal(created.ok, true);
  assert.notEqual(created.afterRevision, created.beforeRevision);
  assert.equal(bb.project.animations.length, 1);
  assert.equal(bb.project.animations[0].uuid, 'anim-idle');
  assert.equal(bb.project.animations[0].loop, 'loop');

  const beforeKeyframe = adapter.getRevision();
  const keyed = applyAnimationBatch(adapter, {
    expectedRevision: beforeKeyframe,
    label: 'Add idle keyframe',
    operations: [
      {
        type: 'animation_add_keyframe',
        animationId: 'anim-idle',
        keyframeId: 'kf-root-0',
        targetId: 'bone-root',
        channel: 'rotation',
        time: 0,
        value: [0, 15, 0],
        easing: 'linear',
      },
    ],
  });
  assert.equal(keyed.ok, true);
  assert.notEqual(keyed.afterRevision, beforeKeyframe, 'keyframe edits must advance the canonical project revision');
  const animator = bb.project.animations[0].animators['bone-root'];
  assert.equal(animator.keyframes.length, 1);
  assert.equal(animator.keyframes[0].uuid, 'kf-root-0');
  assert.equal(animator.keyframes[0].channel, 'rotation');
  assert.equal(animator.keyframes[0].interpolation, 'linear');
  assert.deepEqual(animator.keyframes[0].data_points[0], {x: 0, y: 15, z: 0});
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.begin').length, 2);
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.finish').length, 2);
  assert.equal(bb.events.some(([kind]) => kind === 'undo.cancel'), false);
  assert.ok(bb.events.every(([kind, aspects]) => kind !== 'undo.begin' || Array.isArray(aspects.animations)));
});

test('adapter updates and deletes keyframes/settings and deletes animations without leaking provider serialization', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchAnimationAdapter(bb);
  createAnimation(adapter);
  applyAnimationBatch(adapter, {
    expectedRevision: adapter.getRevision(),
    operations: [{
      type: 'animation_add_keyframe', animationId: 'anim-idle', keyframeId: 'kf-root-0', targetId: 'bone-root',
      channel: 'position', time: 0, value: [0, 0, 0], easing: 'step',
    }],
  });

  applyAnimationBatch(adapter, {
    expectedRevision: adapter.getRevision(),
    operations: [
      {type: 'animation_update_settings', animationId: 'anim-idle', name: 'animation.example.walk', length: 2, loop: 'once'},
      {
        type: 'animation_update_keyframe', animationId: 'anim-idle', keyframeId: 'kf-root-0', targetId: 'bone-root',
        channel: 'position', time: 0.5, value: [1, 2, 3], easing: 'bezier',
      },
    ],
  });
  const animation = bb.project.animations[0];
  const keyframe = animation.animators['bone-root'].keyframes[0];
  assert.equal(animation.name, 'animation.example.walk');
  assert.equal(animation.length, 2);
  assert.equal(animation.loop, 'once');
  assert.equal(keyframe.time, 0.5);
  assert.equal(keyframe.interpolation, 'bezier');
  assert.deepEqual(keyframe.data_points[0], {x: 1, y: 2, z: 3});

  applyAnimationBatch(adapter, {
    expectedRevision: adapter.getRevision(),
    operations: [{type: 'animation_delete_keyframe', animationId: 'anim-idle', keyframeId: 'kf-root-0'}],
  });
  assert.equal(animation.animators['bone-root'].keyframes.length, 0);

  applyAnimationBatch(adapter, {
    expectedRevision: adapter.getRevision(),
    operations: [{type: 'animation_delete', animationId: 'anim-idle'}],
  });
  assert.equal(bb.project.animations.length, 0);
});

test('abstract effect markers fail closed at the generic Blockbench adapter boundary until a provider adapter exists', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchAnimationAdapter(bb);
  createAnimation(adapter);
  const undoCount = bb.events.length;
  assert.throws(() => applyAnimationBatch(adapter, {
    expectedRevision: adapter.getRevision(),
    operations: [{
      type: 'animation_add_effect_marker', animationId: 'anim-idle', markerId: 'marker-1',
      time: 0.25, markerType: 'particle', label: 'muzzle_flash',
    }],
  }), /PROVIDER_ADAPTER_REQUIRED/);
  assert.equal(bb.events.length, undoCount, 'provider-bound marker rejection must happen before Undo');
});

test('preview and pose inspection use editor preview state without mutating asset revision', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchAnimationAdapter(bb);
  createAnimation(adapter);
  const revision = adapter.getRevision();

  const preview = playPreview(adapter, {animationId: 'anim-idle', time: 0.25});
  assert.equal(preview.ok, true);
  assert.equal(preview.animationId, 'anim-idle');
  assert.equal(bb.Animation.selected.uuid, 'anim-idle');
  assert.equal(bb.Animator.previewCalls > 0, true);
  assert.equal(adapter.getRevision(), revision);

  const pose = inspectPose(adapter, {animationId: 'anim-idle', time: 0.5});
  assert.deepEqual(pose.targets['bone-root'].position, [0.5, 0, 0]);
  assert.deepEqual(pose.targets['bone-root'].rotation, [0, 1, 0]);
  assert.deepEqual(pose.targets['bone-root'].scale, [1, 1, 1.5]);
  assert.equal(adapter.getRevision(), revision);

  const stopped = stopPreview(adapter);
  assert.equal(stopped.ok, true);
  assert.equal(bb.project.animations[0].playing, false);
  assert.equal(adapter.getRevision(), revision);
});

test('capture uses an audited camera preset and Screencam without provider export or asset mutation', async () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchAnimationAdapter(bb);
  createAnimation(adapter);
  const revision = adapter.getRevision();

  const capture = await capturePose(adapter, {
    animationId: 'anim-idle',
    time: 0.75,
    cameraPreset: 'isometric_right',
    resolution: [640, 480],
  });
  assert.equal(capture.ok, true);
  assert.equal(capture.dataUrl, 'data:image/png;base64,AAAA');
  assert.equal(capture.cameraPreset, 'isometric_right');
  assert.deepEqual(capture.resolution, [640, 480]);
  assert.deepEqual(bb.Preview.selected.loadedPresets, ['isometric_right']);
  assert.deepEqual(bb.events.find(([kind]) => kind === 'capture').slice(1), [true, {width: 640, height: 480}]);
  assert.equal(adapter.getRevision(), revision);

  assert.throws(() => capturePose(adapter, {
    animationId: 'anim-idle', time: 0, cameraPreset: 'unknown-provider-camera', resolution: [64, 64],
  }), /CAMERA_PRESET_NOT_FOUND/);
});
