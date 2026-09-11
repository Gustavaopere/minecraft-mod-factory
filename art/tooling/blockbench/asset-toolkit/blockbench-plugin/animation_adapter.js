'use strict';

function fail(code, message) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  throw error;
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

function idOf(value) {
  return value && typeof value === 'object' && typeof value.uuid === 'string' && value.uuid ? value.uuid : null;
}

function vector3FromObject(value, fallback) {
  const source = value && typeof value === 'object' ? value : {};
  const output = ['x', 'y', 'z'].map((axis, index) => Number.isFinite(source[axis]) ? source[axis] : fallback[index]);
  return output;
}

function createBlockbenchAnimationAdapter(bb) {
  const project = bb?.Blockbench?.Project;
  if (!project || typeof project !== 'object') fail('NO_PROJECT', 'No Blockbench project is open.');
  if (bb.Blockbench.isWeb !== false) fail('DESKTOP_REQUIRED', 'Animation mutations require desktop Blockbench.');
  if (typeof bb.Animation !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation constructor is unavailable.');
  if (!bb.Undo || ['initEdit', 'finishEdit', 'cancelEdit'].some((name) => typeof bb.Undo[name] !== 'function')) {
    fail('BLOCKBENCH_API_UNAVAILABLE', 'Blockbench Undo API is incomplete.');
  }
  if (!bb.Animator || typeof bb.Animator.preview !== 'function') {
    fail('BLOCKBENCH_API_UNAVAILABLE', 'Animator.preview() is unavailable.');
  }

  let transactionOpen = false;

  function animations() {
    return Array.isArray(bb.Animation.all) ? bb.Animation.all : array(project.animations);
  }

  function groups() {
    return bb.Group && Array.isArray(bb.Group.all) ? bb.Group.all : array(project.groups);
  }

  function findAnimation(animationId) {
    return animations().find((animation) => idOf(animation) === animationId) || null;
  }

  function requireAnimation(animationId) {
    const animation = findAnimation(animationId);
    if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${animationId}" does not exist.`);
    return animation;
  }

  function findTarget(targetId) {
    return groups().find((group) => idOf(group) === targetId) || null;
  }

  function requireTarget(targetId) {
    const target = findTarget(targetId);
    if (!target) fail('ANIMATION_TARGET_NOT_FOUND', `Animation target "${targetId}" does not exist.`);
    return target;
  }

  function animatorsOf(animation) {
    return animation?.animators && typeof animation.animators === 'object'
      ? Object.values(animation.animators).filter(Boolean)
      : [];
  }

  function keyframesOf(animation) {
    const output = [];
    for (const animator of animatorsOf(animation)) {
      for (const keyframe of array(animator.keyframes)) {
        if (keyframe && !output.includes(keyframe)) output.push(keyframe);
      }
    }
    return output;
  }

  function allKeyframes() {
    const output = [];
    for (const animation of animations()) {
      for (const keyframe of keyframesOf(animation)) {
        if (!output.includes(keyframe)) output.push(keyframe);
      }
    }
    return output;
  }

  function findKeyframe(animation, keyframeId) {
    for (const animator of animatorsOf(animation)) {
      const keyframe = array(animator.keyframes).find((entry) => idOf(entry) === keyframeId);
      if (keyframe) return {animator, keyframe};
    }
    return null;
  }

  function keyframeRevisionSnapshot() {
    return animations().map((animation) => ({
      animationId: idOf(animation),
      animators: Object.keys(animation?.animators || {}).sort((left, right) => left.localeCompare(right, 'en')).map((targetId) => ({
        targetId,
        keyframes: array(animation.animators[targetId]?.keyframes).map((keyframe) => ({
          keyframeId: idOf(keyframe),
          channel: typeof keyframe?.channel === 'string' ? keyframe.channel : null,
          time: Number.isFinite(keyframe?.time) ? keyframe.time : null,
          interpolation: typeof keyframe?.interpolation === 'string' ? keyframe.interpolation : null,
          dataPoints: array(keyframe?.data_points).map((point) => ({
            x: point?.x ?? null,
            y: point?.y ?? null,
            z: point?.z ?? null,
          })),
        })),
      })),
    }));
  }

  function getRevision() {
    const {createProjectSnapshot, hashRevision} = require('../live-bridge/project_snapshot.js');
    const baseRevision = createProjectSnapshot(project).projectRevision;
    return hashRevision({baseRevision, animationKeyframes: keyframeRevisionSnapshot()});
  }

  function preflight(operations) {
    const simulated = new Map();
    for (const animation of animations()) {
      const id = idOf(animation);
      if (!id) continue;
      const keyframes = new Map();
      for (const animator of animatorsOf(animation)) {
        for (const keyframe of array(animator.keyframes)) {
          const keyframeId = idOf(keyframe);
          if (keyframeId) keyframes.set(keyframeId, {targetId: idOf(animator), channel: keyframe.channel});
        }
      }
      simulated.set(id, {
        id,
        name: typeof animation.name === 'string' ? animation.name : '',
        length: Number.isFinite(animation.length) ? animation.length : 0,
        keyframes,
      });
    }

    function animationNameExists(name, excludeId = null) {
      const wanted = String(name).toLowerCase();
      return [...simulated.values()].some((entry) => entry.id !== excludeId && entry.name.toLowerCase() === wanted);
    }

    for (const operation of operations) {
      switch (operation.type) {
        case 'animation_create':
          if (simulated.has(operation.id)) fail('DUPLICATE_ANIMATION_ID', `Animation id "${operation.id}" already exists.`);
          if (animationNameExists(operation.name)) fail('DUPLICATE_ANIMATION_NAME', `Animation name "${operation.name}" already exists.`);
          simulated.set(operation.id, {
            id: operation.id,
            name: operation.name,
            length: operation.length,
            keyframes: new Map(),
          });
          break;
        case 'animation_update_settings': {
          const animation = simulated.get(operation.animationId);
          if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
          if (operation.name !== undefined && animationNameExists(operation.name, operation.animationId)) {
            fail('DUPLICATE_ANIMATION_NAME', `Animation name "${operation.name}" already exists.`);
          }
          if (operation.name !== undefined) animation.name = operation.name;
          if (operation.length !== undefined) animation.length = operation.length;
          break;
        }
        case 'animation_delete':
          if (!simulated.has(operation.animationId)) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
          simulated.delete(operation.animationId);
          break;
        case 'animation_add_keyframe': {
          const animation = simulated.get(operation.animationId);
          if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
          requireTarget(operation.targetId);
          if (animation.keyframes.has(operation.keyframeId)) {
            fail('DUPLICATE_KEYFRAME_ID', `Keyframe "${operation.keyframeId}" already exists in animation "${operation.animationId}".`);
          }
          if (operation.time > animation.length) {
            fail('KEYFRAME_OUTSIDE_ANIMATION', `Keyframe time ${operation.time} exceeds animation length ${animation.length}.`);
          }
          animation.keyframes.set(operation.keyframeId, {targetId: operation.targetId, channel: operation.channel});
          break;
        }
        case 'animation_update_keyframe': {
          const animation = simulated.get(operation.animationId);
          if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
          requireTarget(operation.targetId);
          if (!animation.keyframes.has(operation.keyframeId)) {
            fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist in animation "${operation.animationId}".`);
          }
          if (operation.time > animation.length) {
            fail('KEYFRAME_OUTSIDE_ANIMATION', `Keyframe time ${operation.time} exceeds animation length ${animation.length}.`);
          }
          animation.keyframes.set(operation.keyframeId, {targetId: operation.targetId, channel: operation.channel});
          break;
        }
        case 'animation_delete_keyframe': {
          const animation = simulated.get(operation.animationId);
          if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
          if (!animation.keyframes.has(operation.keyframeId)) {
            fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist in animation "${operation.animationId}".`);
          }
          animation.keyframes.delete(operation.keyframeId);
          break;
        }
        case 'animation_add_effect_marker':
        case 'animation_delete_effect_marker':
          fail('PROVIDER_ADAPTER_REQUIRED', 'Abstract PR5 effect markers require a provider adapter before Blockbench serialization.');
          break;
        default:
          fail('UNSUPPORTED_ANIMATION_OPERATION', `Animation operation "${operation.type}" is not supported by the Blockbench adapter.`);
      }
    }
    return true;
  }

  function undoAspects() {
    return {
      animations: animations().slice(),
      keyframes: allKeyframes().slice(),
    };
  }

  function beginTransaction() {
    if (transactionOpen) fail('TRANSACTION_ALREADY_OPEN', 'A Blockbench Undo transaction is already open.');
    bb.Undo.initEdit(undoAspects());
    transactionOpen = true;
  }

  function finishTransaction(label) {
    if (!transactionOpen) fail('NO_ACTIVE_TRANSACTION', 'No Blockbench Undo transaction is open.');
    bb.Undo.finishEdit(label, undoAspects());
    transactionOpen = false;
  }

  function cancelTransaction(revert) {
    if (!transactionOpen) return;
    try {
      bb.Undo.cancelEdit(revert === true);
    } finally {
      transactionOpen = false;
    }
  }

  function addKeyframe(animation, operation) {
    const target = requireTarget(operation.targetId);
    if (typeof animation.getBoneAnimator !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.getBoneAnimator() is unavailable.');
    }
    const animator = animation.getBoneAnimator(target);
    if (!animator || typeof animator.addKeyframe !== 'function') {
      fail('ANIMATION_TARGET_UNSUPPORTED', `Target "${operation.targetId}" does not expose a mutable animation channel.`);
    }
    const keyframe = animator.addKeyframe({
      channel: operation.channel,
      time: operation.time,
      interpolation: operation.easing,
      data_points: [{x: operation.value[0], y: operation.value[1], z: operation.value[2]}],
    }, operation.keyframeId);
    if (!keyframe) fail('KEYFRAME_CREATE_FAILED', `Blockbench did not create keyframe "${operation.keyframeId}".`);
    return idOf(keyframe) || operation.keyframeId;
  }

  function applyOperation(operation) {
    switch (operation.type) {
      case 'animation_create': {
        const animation = new bb.Animation({
          uuid: operation.id,
          name: operation.name,
          length: operation.length,
          loop: operation.loop,
        });
        if (typeof animation.add !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.add() is unavailable.');
        animation.add(false);
        return idOf(animation) || operation.id;
      }
      case 'animation_update_settings': {
        const animation = requireAnimation(operation.animationId);
        if (operation.name !== undefined) animation.name = operation.name;
        if (operation.length !== undefined) {
          if (typeof animation.setLength !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.setLength() is unavailable.');
          animation.setLength(operation.length);
        }
        if (operation.loop !== undefined) {
          if (typeof animation.setLoop !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.setLoop() is unavailable.');
          animation.setLoop(operation.loop, false);
        }
        return idOf(animation) || operation.animationId;
      }
      case 'animation_delete': {
        const animation = requireAnimation(operation.animationId);
        if (typeof animation.remove !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.remove() is unavailable.');
        animation.remove(false);
        return operation.animationId;
      }
      case 'animation_add_keyframe':
        return addKeyframe(requireAnimation(operation.animationId), operation);
      case 'animation_update_keyframe': {
        const animation = requireAnimation(operation.animationId);
        const found = findKeyframe(animation, operation.keyframeId);
        if (!found) fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist.`);
        if (typeof found.keyframe.remove !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Keyframe.remove() is unavailable.');
        found.keyframe.remove();
        return addKeyframe(animation, operation);
      }
      case 'animation_delete_keyframe': {
        const animation = requireAnimation(operation.animationId);
        const found = findKeyframe(animation, operation.keyframeId);
        if (!found) fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist.`);
        if (typeof found.keyframe.remove !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Keyframe.remove() is unavailable.');
        found.keyframe.remove();
        return operation.keyframeId;
      }
      case 'animation_add_effect_marker':
      case 'animation_delete_effect_marker':
        fail('PROVIDER_ADAPTER_REQUIRED', 'Abstract PR5 effect markers require a provider adapter before Blockbench serialization.');
        break;
      default:
        fail('UNSUPPORTED_ANIMATION_OPERATION', `Animation operation "${operation.type}" is not supported by the Blockbench adapter.`);
    }
    return null;
  }

  function selectPreviewAnimation(request) {
    const animation = requireAnimation(request.animationId);
    if (request.time > animation.length) {
      fail('PREVIEW_TIME_OUT_OF_RANGE', `Preview time ${request.time} exceeds animation length ${animation.length}.`);
    }
    if (typeof animation.select !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.select() is unavailable.');
    animation.select();
    animation.time = request.time;
    bb.Animator.preview(false);
    return animation;
  }

  function playPreview(request) {
    const animation = selectPreviewAnimation(request);
    if (typeof animation.togglePlayingState === 'function') animation.togglePlayingState(true);
    return Object.freeze({ok: true, animationId: request.animationId, time: request.time});
  }

  function stopPreview() {
    const animation = bb.Animation.selected || null;
    if (animation && typeof animation.togglePlayingState === 'function') animation.togglePlayingState(false);
    if (typeof bb.Animator.showDefaultPose === 'function') bb.Animator.showDefaultPose(false);
    return Object.freeze({ok: true, animationId: animation ? idOf(animation) : null});
  }

  function inspectPose(request) {
    selectPreviewAnimation(request);
    const targets = {};
    for (const group of groups()) {
      const targetId = idOf(group);
      if (!targetId || !group.mesh) continue;
      targets[targetId] = Object.freeze({
        position: Object.freeze(vector3FromObject(group.mesh.position, [0, 0, 0])),
        rotation: Object.freeze(vector3FromObject(group.mesh.rotation, [0, 0, 0])),
        scale: Object.freeze(vector3FromObject(group.mesh.scale, [1, 1, 1])),
      });
    }
    return Object.freeze({
      animationId: request.animationId,
      time: request.time,
      targets: Object.freeze(targets),
    });
  }

  function capturePose(request) {
    selectPreviewAnimation(request);
    const presets = array(bb.DefaultCameraPresets);
    const preset = presets.find((entry) => entry && entry.id === request.cameraPreset);
    if (!preset) fail('CAMERA_PRESET_NOT_FOUND', `Camera preset "${request.cameraPreset}" is not available.`);
    const preview = bb?.Preview?.selected;
    if (!preview || typeof preview.loadAnglePreset !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', 'Preview.selected.loadAnglePreset() is unavailable.');
    }
    if (!bb.Screencam || typeof bb.Screencam.screenshotPreview !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', 'Screencam.screenshotPreview() is unavailable.');
    }
    preview.loadAnglePreset(preset);
    return new Promise((resolve, reject) => {
      try {
        bb.Screencam.screenshotPreview(preview, {
          width: request.resolution[0],
          height: request.resolution[1],
        }, (dataUrl) => {
          resolve(Object.freeze({
            ok: true,
            animationId: request.animationId,
            time: request.time,
            cameraPreset: request.cameraPreset,
            resolution: Object.freeze(request.resolution.slice()),
            dataUrl,
          }));
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  return Object.freeze({
    getRevision,
    preflight,
    beginTransaction,
    applyOperation,
    finishTransaction,
    cancelTransaction,
    playPreview,
    stopPreview,
    inspectPose,
    capturePose,
  });
}

module.exports = {createBlockbenchAnimationAdapter};
