'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

class RealHandoffEvidenceError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'RealHandoffEvidenceError';
    this.code = code;
  }
}

const fail = (code, message) => { throw new RealHandoffEvidenceError(code, message); };
const readJson = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));
const sha256 = (buffer) => crypto.createHash('sha256').update(buffer).digest('hex');

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort((left, right) => left.localeCompare(right, 'en')).map((key) => [key, canonical(value[key])]));
  }
  return value;
}

function semanticEqual(left, right) {
  return JSON.stringify(canonical(left)) === JSON.stringify(canonical(right));
}

function loadEvidence(root = __dirname) {
  const manifest = readJson(path.join(root, 'MANIFEST.json'));
  const byKind = (entries, kind) => entries.find((entry) => entry.kind === kind);
  const loadKind = (kind) => {
    const actual = byKind(manifest.actualExports || [], kind);
    const expected = byKind(manifest.expectedExports || [], kind);
    const alias = byKind(manifest.canonicalExportAliases || [], kind);
    if (!actual || !expected || !alias) fail('MISSING_EVIDENCE_DECLARATION', `${kind} evidence declaration missing`);
    const rawPath = path.join(root, actual.path);
    const expectedPath = path.join(root, expected.path);
    const aliasPath = path.join(root, alias.path);
    for (const [label, file] of [['raw', rawPath], ['expected', expectedPath], ['alias', aliasPath]]) {
      if (!fs.existsSync(file)) fail('MISSING_EVIDENCE_FILE', `${kind} ${label} file missing: ${path.relative(root, file)}`);
    }
    return {
      declaration: actual,
      expectedDeclaration: expected,
      aliasDeclaration: alias,
      rawBuffer: fs.readFileSync(rawPath),
      rawJson: readJson(rawPath),
      expectedJson: readJson(expectedPath),
      aliasBuffer: fs.readFileSync(aliasPath),
      aliasJson: readJson(aliasPath),
    };
  };
  return {manifest, model: loadKind('model'), animation: loadKind('animation')};
}

function vectorLeaf(value, field) {
  if (!value || typeof value !== 'object' || !Array.isArray(value.vector) || value.vector.length !== 3 || !value.vector.every(Number.isFinite)) {
    fail('INVALID_REAL_ANIMATION_VECTOR', `${field} must be {vector:[x,y,z]} with finite numbers`);
  }
  return value.vector;
}

function validateModel(model) {
  const geo = model.rawJson;
  if (geo.format_version !== '1.12.0') fail('REAL_MODEL_FORMAT_DRIFT', 'expected format_version 1.12.0');
  const entries = geo['minecraft:geometry'];
  if (!Array.isArray(entries) || entries.length !== 1) fail('REAL_MODEL_GEOMETRY_DRIFT', 'expected exactly one geometry entry');
  const geometry = entries[0];
  const desc = geometry.description || {};
  if (desc.identifier !== 'geometry.golden_sample_mob' || desc.texture_width !== 32 || desc.texture_height !== 32) {
    fail('REAL_MODEL_IDENTITY_DRIFT', 'identifier or texture resolution drifted');
  }
  if (desc.visible_bounds_width !== 2 || desc.visible_bounds_height !== 2.5 || !semanticEqual(desc.visible_bounds_offset, [0, 0.75, 0])) {
    fail('REAL_MODEL_BOUNDS_DRIFT', 'real exporter bounds no longer match observed GeckoLib 4.2.5 output');
  }
  const bones = Object.fromEntries((geometry.bones || []).map((bone) => [bone.name, bone]));
  const names = Object.keys(bones);
  if (!semanticEqual(names, ['root', 'body', 'head', 'left_leg', 'right_leg'])) fail('REAL_MODEL_BONES_DRIFT', 'bone order/names drifted');
  if (!semanticEqual(bones.head?.locators?.focus, [0, 18, -4])) fail('REAL_MODEL_LOCATOR_DRIFT', 'focus locator drifted');
  if (!semanticEqual(bones.left_leg?.pivot, [-1.5, 4, 0]) || !semanticEqual(bones.left_leg?.cubes?.[0]?.origin, [-3, 0, -2])) {
    fail('REAL_MODEL_X_MIRROR_DRIFT', 'left_leg exporter X transform drifted');
  }
  if (!semanticEqual(bones.right_leg?.pivot, [1.5, 4, 0]) || !semanticEqual(bones.right_leg?.cubes?.[0]?.origin, [0, 0, -2])) {
    fail('REAL_MODEL_X_MIRROR_DRIFT', 'right_leg exporter X transform drifted');
  }
}

function validateAnimation(animation) {
  const doc = animation.rawJson;
  if (doc.format_version !== '1.8.0') fail('REAL_ANIMATION_FORMAT_DRIFT', 'expected format_version 1.8.0');
  const animations = doc.animations || {};
  const names = Object.keys(animations).sort((left, right) => left.localeCompare(right, 'en'));
  if (!semanticEqual(names, ['animation.golden_sample_mob.idle', 'animation.golden_sample_mob.walk'])) {
    fail('REAL_ANIMATION_SET_DRIFT', 'idle/walk animation set drifted');
  }
  const idle = animations['animation.golden_sample_mob.idle'];
  const walk = animations['animation.golden_sample_mob.walk'];
  if (idle?.loop !== true || idle?.animation_length !== 2 || walk?.loop !== true || walk?.animation_length !== 1) {
    fail('REAL_ANIMATION_METADATA_DRIFT', 'loop or animation_length drifted');
  }
  const idleExpected = {'0.0':[0,0,0], '1.0':[0,-5,0], '2.0':[0,0,0]};
  for (const [time, expected] of Object.entries(idleExpected)) {
    const actual = vectorLeaf(idle?.bones?.head?.rotation?.[time], `idle.head.rotation.${time}`);
    if (!semanticEqual(actual, expected)) fail('REAL_ANIMATION_COORDINATE_DRIFT', `idle ${time} drifted`);
  }
  const leftExpected = {'0.0':[-25,0,0], '0.5':[25,0,0], '1.0':[-25,0,0]};
  const rightExpected = {'0.0':[25,0,0], '0.5':[-25,0,0], '1.0':[25,0,0]};
  for (const [bone, expectedMap] of [['left_leg', leftExpected], ['right_leg', rightExpected]]) {
    for (const [time, expected] of Object.entries(expectedMap)) {
      const actual = vectorLeaf(walk?.bones?.[bone]?.rotation?.[time], `walk.${bone}.rotation.${time}`);
      if (!semanticEqual(actual, expected)) fail('REAL_ANIMATION_COORDINATE_DRIFT', `walk ${bone} ${time} drifted`);
    }
  }
}

function validateRuntimeEvidence(runtimeEvidence) {
  if (!runtimeEvidence || typeof runtimeEvidence !== 'object') fail('INVALID_RUNTIME_EVIDENCE', 'durable runtime evidence object is required');
  if (
    runtimeEvidence.classification !== 'PASS' ||
    runtimeEvidence.commit !== '33f0322fd806d593da4e3063db93b709dbe878da' ||
    runtimeEvidence.workflowRunId !== 34710808440 ||
    runtimeEvidence.jobId !== 103599143647
  ) {
    fail('INVALID_RUNTIME_PROVENANCE', 'runtime proof provenance drifted from the validated GitHub Actions evidence');
  }
  const expectedTarget = {minecraft:'1.21.1', neoforge:'21.1.248', java:21, geckolib:'4.9.2'};
  if (!semanticEqual(runtimeEvidence.target, expectedTarget)) fail('INVALID_RUNTIME_TARGET', 'runtime proof target drifted');
  const server = runtimeEvidence.server || {};
  if (server.gameTest !== 'PASS' || server.player_connected !== true || server.mob_spawned !== true) {
    fail('INVALID_RUNTIME_SERVER_EVIDENCE', 'dedicated-server/GameTest runtime proof is incomplete');
  }
  const client = runtimeEvidence.client || {};
  if (
    client.client_joined !== true ||
    client.renderer_invoked !== true ||
    client.baked_model_observed !== true ||
    client.texture_resolved !== true ||
    client.animation_motion_observed !== true ||
    client.texture !== 'i3_golden_mod:textures/entity/golden_sample_mob.png' ||
    !Number.isFinite(client.head_rotation_y) ||
    Math.abs(client.head_rotation_y) <= 0.0001
  ) {
    fail('INVALID_RUNTIME_CLIENT_EVIDENCE', 'live-client renderer/model/texture/animation proof is incomplete');
  }
  return runtimeEvidence;
}

function validateRealHandoffEvidence(input = loadEvidence()) {
  const {manifest, model, animation} = input;
  if (manifest.state !== 'REAL_HANDOFF_VALIDATED') fail('INVALID_REAL_HANDOFF_STATE', 'completed handoff must use the existing REAL_HANDOFF_VALIDATED domain state');
  const handoff = manifest.realHandoff || {};
  const requiredTrue = ['editorOpened', 'sourceRoundTripValidated', 'exporterProduced', 'reopenValidated', 'runtimeValidated', 'f4I6Evidence'];
  if (requiredTrue.some((key) => handoff[key] !== true)) {
    fail('INVALID_REAL_HANDOFF_FLAGS', 'completed real handoff requires every authoring/export/reopen/runtime/I6 gate');
  }
  const runtimeEvidence = validateRuntimeEvidence(handoff.runtimeEvidence);
  const manual = manifest.manualEvidence || {};
  const expectedAnimationNames = ['animation.golden_sample_mob.idle', 'animation.golden_sample_mob.walk'];
  if (
    manual.blockbenchVersion !== '5.1.6' ||
    manual.geckolibPluginVersion !== '4.2.5' ||
    manual.sourceOpened !== true ||
    manual.roundTripReopened !== true ||
    manual.exportedModelReopened !== true ||
    manual.exportedAnimationImported !== true ||
    !semanticEqual(manual.importedAnimationNames, expectedAnimationNames) ||
    manual.idlePlaybackValidated !== true ||
    manual.idlePlaybackObservation !== 'NO_VISIBLE_MOTION' ||
    manual.walkPlaybackValidated !== true ||
    manual.walkPlaybackObservation !== 'VISIBLE_MOTION'
  ) {
    fail('INVALID_MANUAL_EVIDENCE', 'Blockbench/plugin/open/round-trip/export-reopen/playback evidence drifted');
  }
  for (const [kind, evidence] of [['model', model], ['animation', animation]]) {
    if (evidence.declaration.origin !== 'BLOCKBENCH_5_1_6_GECKOLIB_4_2_5_EXPORTER') fail('INVALID_EXPORT_ORIGIN', `${kind} origin drifted`);
    if (sha256(evidence.rawBuffer) !== evidence.declaration.sha256) fail('ACTUAL_EXPORT_HASH_DRIFT', `${kind} raw exporter bytes differ from manifest hash`);
    if (evidence.aliasDeclaration.classification !== 'FACTORY_CANONICAL_ALIAS_NOT_EXPORTER_ORIGIN' || evidence.aliasDeclaration.sourcePath !== evidence.declaration.path) {
      fail('INVALID_CANONICAL_ALIAS', `${kind} alias classification/source drifted`);
    }
    if (!evidence.rawBuffer.equals(evidence.aliasBuffer)) fail('CANONICAL_ALIAS_BYTE_DRIFT', `${kind} alias must remain byte-identical to raw exporter output`);
    if (!semanticEqual(evidence.rawJson, evidence.expectedJson)) fail('EXPORTER_CONTRACT_DIVERGENCE', `${kind} actual export diverges from reconciled expected contract`);
    if (!semanticEqual(evidence.rawJson, evidence.aliasJson)) fail('CANONICAL_ALIAS_SEMANTIC_DRIFT', `${kind} alias semantics drifted`);
  }
  validateModel(model);
  validateAnimation(animation);
  return Object.freeze({
    ok: true,
    modelSha256: sha256(model.rawBuffer),
    animationSha256: sha256(animation.rawBuffer),
    exporterProduced: true,
    reopenValidated: true,
    runtimeValidated: true,
    f4I6Evidence: true,
    runtimeEvidence,
  });
}

if (require.main === module) process.stdout.write(`${JSON.stringify(validateRealHandoffEvidence(), null, 2)}\n`);
module.exports = {RealHandoffEvidenceError, loadEvidence, validateRealHandoffEvidence};
