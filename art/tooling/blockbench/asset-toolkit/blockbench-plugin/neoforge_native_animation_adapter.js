'use strict';

const neoforgeNative = require('../core/provider-adapter/neoforge_native_animation_adapter.js');

function fail(code, message) {
  throw new neoforgeNative.NeoForgeNativeAnimationContractError(code, message);
}

function normalizedSourcePath(value) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED', 'Active Blockbench project must be saved as a .bbmodel before native animation export.');
  }
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith('.bbmodel')) {
    fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED', 'Active Blockbench project source must remain a .bbmodel file.');
  }
  return normalized;
}

function createBlockbenchNeoForgeNativeAnimationAdapter(bb) {
  if (!bb || typeof bb !== 'object') {
    fail('NEOFORGE_NATIVE_ANIMATION_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  }
  if (bb.Blockbench?.isWeb !== false) {
    fail('NEOFORGE_NATIVE_ANIMATION_DESKTOP_REQUIRED', 'NeoForge native animation export requires desktop Blockbench.');
  }
  const project = bb.Blockbench?.Project;
  if (!project || typeof project !== 'object') {
    fail('NEOFORGE_NATIVE_ANIMATION_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
  }
  const savedSourcePath = normalizedSourcePath(project.save_path);
  if (typeof bb.BoneAnimator !== 'function') {
    fail('NEOFORGE_NATIVE_ANIMATION_BLOCKBENCH_API_UNAVAILABLE', 'Blockbench BoneAnimator API is required.');
  }

  const trustedPreviews = new WeakSet();

  function sourcePath() {
    return savedSourcePath;
  }

  function animations() {
    if (Array.isArray(bb.Animation?.all)) return bb.Animation.all;
    return Array.isArray(project.animations) ? project.animations : [];
  }

  function requireAnimation(animationId) {
    if (typeof animationId !== 'string' || animationId.length === 0) {
      fail('NEOFORGE_NATIVE_ANIMATION_NOT_FOUND', 'animationId must identify an active Blockbench animation.');
    }
    const animation = animations().find((entry) => entry && entry.uuid === animationId) || null;
    if (!animation) fail('NEOFORGE_NATIVE_ANIMATION_NOT_FOUND', `Animation ${JSON.stringify(animationId)} does not exist.`);
    return animation;
  }

  function keyframeVector(keyframe, field) {
    if (!keyframe || typeof keyframe.get !== 'function') {
      fail('NEOFORGE_NATIVE_ANIMATION_KEYFRAME_UNAVAILABLE', `${field} does not expose Blockbench keyframe values.`);
    }
    return ['x', 'y', 'z'].map((axis) => keyframe.get(axis));
  }

  function providerNeutralAnimation(animation) {
    const channels = [];
    for (const animator of Object.values(animation.animators || {})) {
      if (!(animator instanceof bb.BoneAnimator)) {
        fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_ANIMATOR', 'Only audited BoneAnimator transform channels can be exported to NeoForge native JSON.');
      }
      if (typeof animator.name !== 'string' || animator.name.length === 0) {
        fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_ANIMATOR', 'Each exported BoneAnimator must expose its bone name.');
      }
      for (const channel of ['position', 'rotation', 'scale']) {
        const keyframes = Array.isArray(animator[channel]) ? animator[channel] : [];
        if (keyframes.length === 0) continue;
        channels.push({
          bone: animator.name,
          channel,
          keyframes: keyframes.map((keyframe, index) => ({
            time: keyframe?.time,
            value: keyframeVector(keyframe, `${animator.name}.${channel}[${index}]`),
            easing: keyframe?.interpolation,
          })),
        });
      }
    }
    return {
      length: animation.length,
      loop: animation.loop,
      channels,
      effectMarkers: Array.isArray(animation.markers) ? animation.markers : [],
    };
  }

  function previewExport(request) {
    if (!request || typeof request !== 'object' || Array.isArray(request)) {
      fail('INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_PLAN', 'Export request must be an object.');
    }
    const plan = neoforgeNative.createNeoForgeNativeAnimationExportPlan({...request, sourcePath: savedSourcePath});
    const animation = requireAnimation(request.animationId);
    const document = neoforgeNative.serializeNeoForgeNativeAnimation(providerNeutralAnimation(animation));
    const artifact = Object.freeze({kind: 'animation', path: plan.outputPath, document});
    const preview = Object.freeze({
      plan,
      artifacts: Object.freeze([artifact]),
      runtimeEvidence: 'UNPROVEN',
    });
    trustedPreviews.add(preview);
    return preview;
  }

  function stageExport(preview, writer) {
    if (!preview || typeof preview !== 'object' || !trustedPreviews.has(preview)) {
      fail('INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_PREVIEW', 'Only a validated preview produced by this adapter can be staged.');
    }
    if (!writer || typeof writer.writeText !== 'function') {
      fail('INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_WRITER', 'Export writer must provide writeText(path, content).');
    }
    for (const artifact of preview.artifacts) {
      if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
        fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_OVERWRITE_FORBIDDEN', 'Native animation staging must never overwrite the source .bbmodel.');
      }
      neoforgeNative.validateNeoForgeNativeAnimationDocument(artifact.document);
      writer.writeText(artifact.path, `${JSON.stringify(artifact.document, null, 2)}\n`);
    }
    return Object.freeze({
      ok: true,
      staged: preview.artifacts.length,
      sourcePath: preview.plan.sourcePath,
      preserveSource: true,
      runtimeEvidence: 'UNPROVEN',
    });
  }

  return Object.freeze({sourcePath, previewExport, stageExport});
}

module.exports = {
  createBlockbenchNeoForgeNativeAnimationAdapter,
};
