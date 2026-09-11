'use strict';

const crypto = require('node:crypto');
const {validateProject} = require('../validator/validator.js');
const {createDeterministicReport} = require('../report/report.js');
const {getProviderProfile} = require('../provider-profile/provider_profiles.js');

const TARGET = Object.freeze({
  minecraftVersion: '1.21.1',
  loader: 'neoforge',
  loaderVersion: '21.1.248',
  javaVersion: '21',
});

function manifestError(code, message) {
  const error = new Error(message || code);
  error.code = code;
  return error;
}

function requiredString(value, code) {
  if (typeof value !== 'string' || !value.trim()) throw manifestError(code, code);
  return value.trim();
}

function compareText(left, right) {
  return String(left).localeCompare(String(right), 'en', {sensitivity: 'variant', numeric: false});
}

function deepFreeze(value) {
  if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const child of Object.values(value)) deepFreeze(child);
  return value;
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort(compareText).map((key) => [key, canonical(value[key])]));
  }
  return value;
}

function contentBytes(value, code) {
  if (typeof value === 'string') return value;
  if (typeof Buffer !== 'undefined' && Buffer.isBuffer && Buffer.isBuffer(value)) return value;
  if (value instanceof Uint8Array) return value;
  throw manifestError(code, code);
}

function sha256(value, code = 'ARTIFACT_CONTENT_REQUIRED') {
  return `sha256:${crypto.createHash('sha256').update(contentBytes(value, code)).digest('hex')}`;
}

function validSha256(value) {
  return typeof value === 'string' && /^sha256:[0-9a-f]{64}$/.test(value);
}

function artifactHash(entry, contentCode) {
  if (validSha256(entry?.sha256)) return entry.sha256;
  return sha256(entry?.content, contentCode);
}

function normalizeRelativePath(value) {
  const raw = requiredString(value, 'EXPORT_PATH_REQUIRED').replace(/\\/g, '/');
  if (raw.startsWith('/') || /^[A-Za-z]:\//.test(raw)) {
    throw manifestError('EXPORT_PATH_OUTSIDE_ALLOWLISTED_ROOT', raw);
  }
  const output = [];
  for (const part of raw.split('/')) {
    if (!part || part === '.') continue;
    if (part === '..') throw manifestError('EXPORT_PATH_OUTSIDE_ALLOWLISTED_ROOT', raw);
    output.push(part);
  }
  if (!output.length) throw manifestError('EXPORT_PATH_REQUIRED', raw);
  return output.join('/');
}

function normalizeRootPath(value) {
  const raw = requiredString(value, 'EXPORT_ROOT_PATH_REQUIRED').replace(/\\/g, '/').replace(/\/+$/g, '');
  if (!raw.startsWith('/') && !/^[A-Za-z]:\//.test(raw)) {
    throw manifestError('EXPORT_ROOT_MUST_BE_ABSOLUTE', raw);
  }
  const parts = raw.split('/');
  if (parts.includes('..')) throw manifestError('EXPORT_ROOT_PATH_INVALID', raw);
  return raw;
}

function normalizeRoots(entries) {
  if (!Array.isArray(entries) || entries.length === 0) throw manifestError('EXPORT_ROOT_REQUIRED');
  const seen = new Set();
  const roots = entries.map((entry) => {
    const id = requiredString(entry?.id, 'EXPORT_ROOT_ID_REQUIRED');
    if (seen.has(id)) throw manifestError('DUPLICATE_EXPORT_ROOT', id);
    seen.add(id);
    const allowKinds = Array.isArray(entry?.allowKinds)
      ? [...new Set(entry.allowKinds.map((kind) => requiredString(kind, 'EXPORT_ROOT_KIND_REQUIRED')))].sort(compareText)
      : [];
    if (!allowKinds.length) throw manifestError('EXPORT_ROOT_KIND_REQUIRED', id);
    return {id, path: normalizeRootPath(entry.path), allowKinds};
  });
  return roots.sort((a, b) => compareText(a.id, b.id));
}

function rootMap(roots) {
  return new Map(roots.map((root) => [root.id, root]));
}

function normalizeStaging(value, rootsById) {
  if (!value || typeof value !== 'object') throw manifestError('STAGING_REQUIRED');
  const rootId = requiredString(value.rootId, 'STAGING_ROOT_REQUIRED');
  if (!rootsById.has(rootId)) throw manifestError('STAGING_ROOT_NOT_ALLOWLISTED', rootId);
  const state = requiredString(value.state, 'STAGING_STATE_REQUIRED');
  if (!['PLANNED', 'STAGED', 'VALIDATED', 'PROMOTED'].includes(state)) throw manifestError('STAGING_STATE_INVALID', state);
  return {rootId, relativePath: normalizeRelativePath(value.relativePath), state};
}

function normalizeExportArtifacts(outputs, rootsById) {
  if (!Array.isArray(outputs)) throw manifestError('EXPORT_OUTPUTS_INVALID');
  const seen = new Set();
  const artifacts = outputs.map((entry) => {
    const kind = requiredString(entry?.kind, 'EXPORT_OUTPUT_KIND_REQUIRED');
    const rootId = requiredString(entry?.rootId, 'EXPORT_OUTPUT_ROOT_REQUIRED');
    const root = rootsById.get(rootId);
    if (!root) throw manifestError('EXPORT_OUTPUT_ROOT_NOT_ALLOWLISTED', rootId);
    if (!root.allowKinds.includes(kind)) throw manifestError('EXPORT_KIND_NOT_ALLOWLISTED', `${rootId}:${kind}`);
    const relativePath = normalizeRelativePath(entry.relativePath);
    const key = `${rootId}:${relativePath}`;
    if (seen.has(key)) throw manifestError('EXPORT_OUTPUT_COLLISION', key);
    seen.add(key);
    return {
      key,
      kind,
      rootId,
      relativePath,
      sha256: artifactHash(entry, 'EXPORT_OUTPUT_CONTENT_REQUIRED'),
    };
  });
  return artifacts.sort((a, b) => compareText(a.key, b.key));
}

function normalizeSourceArtifacts(entries) {
  if (!Array.isArray(entries)) throw manifestError('SOURCE_ARTIFACTS_INVALID');
  return entries.map((entry) => {
    const kind = requiredString(entry?.kind, 'SOURCE_ARTIFACT_KIND_REQUIRED');
    const path = requiredString(entry?.path, 'SOURCE_ARTIFACT_PATH_REQUIRED').replace(/\\/g, '/');
    if (kind === 'blockbench_source' && !path.toLowerCase().endsWith('.bbmodel')) {
      throw manifestError('BLOCKBENCH_SOURCE_MUST_BE_BBMODEL', path);
    }
    return {
      kind,
      path,
      preserve: entry?.preserve === true,
      sha256: artifactHash(entry, 'SOURCE_ARTIFACT_CONTENT_REQUIRED'),
    };
  }).sort((a, b) => compareText(`${a.kind}:${a.path}`, `${b.kind}:${b.path}`));
}

function normalizeCaptureEvidence(entries) {
  if (!Array.isArray(entries)) throw manifestError('CAPTURE_EVIDENCE_INVALID');
  return entries.map((entry) => {
    const id = requiredString(entry?.id, 'CAPTURE_ID_REQUIRED');
    const resolution = Array.isArray(entry?.resolution) && entry.resolution.length >= 2
      && entry.resolution.slice(0, 2).every((value) => Number.isInteger(value) && value > 0)
      ? entry.resolution.slice(0, 2)
      : null;
    if (!resolution) throw manifestError('CAPTURE_RESOLUTION_INVALID', id);
    return {
      id,
      cameraPreset: requiredString(entry?.cameraPreset, 'CAPTURE_CAMERA_PRESET_REQUIRED'),
      animation: typeof entry?.animation === 'string' && entry.animation.trim() ? entry.animation.trim() : null,
      animationTime: Number.isFinite(entry?.animationTime) ? entry.animationTime : null,
      resolution,
      timestamp: typeof entry?.timestamp === 'string' && entry.timestamp.trim() ? entry.timestamp.trim() : null,
      sha256: artifactHash(entry, 'CAPTURE_CONTENT_REQUIRED'),
    };
  }).sort((a, b) => compareText(a.id, b.id));
}

function normalizeEvidence(value, allowedStates, code) {
  if (!value || typeof value !== 'object') throw manifestError(code, code);
  const status = requiredString(value.status, code);
  if (!allowedStates.includes(status)) throw manifestError(code, status);
  return {
    status,
    evidenceId: typeof value.evidenceId === 'string' && value.evidenceId.trim() ? value.evidenceId.trim() : null,
    ...(Array.isArray(value.checks) ? {checks: [...new Set(value.checks.map((item) => requiredString(item, code)))].sort(compareText)} : {}),
  };
}

function normalizeRuntimeTarget(value) {
  if (!value || typeof value !== 'object') throw manifestError('RUNTIME_TARGET_REQUIRED');
  const target = {
    minecraftVersion: requiredString(value.minecraftVersion, 'RUNTIME_TARGET_REQUIRED'),
    loader: requiredString(value.loader, 'RUNTIME_TARGET_REQUIRED'),
    loaderVersion: requiredString(value.loaderVersion, 'RUNTIME_TARGET_REQUIRED'),
    javaVersion: requiredString(value.javaVersion, 'RUNTIME_TARGET_REQUIRED'),
  };
  for (const [key, expected] of Object.entries(TARGET)) {
    if (target[key] !== expected) throw manifestError('RUNTIME_TARGET_UNSUPPORTED', `${key}:${target[key]}`);
  }
  return target;
}

function normalizeHandoffs(entries, rootsById) {
  if (!Array.isArray(entries)) throw manifestError('HANDOFF_DESTINATIONS_INVALID');
  return entries.map((entry) => {
    const rootId = requiredString(entry?.rootId, 'HANDOFF_ROOT_REQUIRED');
    if (!rootsById.has(rootId)) throw manifestError('HANDOFF_ROOT_NOT_ALLOWLISTED', rootId);
    const result = {
      kind: requiredString(entry?.kind, 'HANDOFF_KIND_REQUIRED'),
      rootId,
    };
    if (typeof entry?.namespace === 'string' && entry.namespace.trim()) result.namespace = entry.namespace.trim();
    return result;
  }).sort((a, b) => compareText(JSON.stringify(canonical(a)), JSON.stringify(canonical(b))));
}

function previousArtifactMap(entries) {
  if (!Array.isArray(entries)) throw manifestError('PREVIOUS_EXPORT_ARTIFACTS_INVALID');
  const result = new Map();
  for (const entry of entries) {
    const key = typeof entry?.key === 'string' && entry.key
      ? entry.key
      : `${requiredString(entry?.rootId, 'PREVIOUS_EXPORT_ROOT_REQUIRED')}:${normalizeRelativePath(entry?.relativePath)}`;
    if (result.has(key)) throw manifestError('DUPLICATE_PREVIOUS_EXPORT_ARTIFACT', key);
    if (!validSha256(entry?.sha256)) throw manifestError('PREVIOUS_EXPORT_HASH_INVALID', key);
    result.set(key, entry.sha256);
  }
  return result;
}

function createSemanticDiff(previousEntries, currentEntries) {
  const previous = previousArtifactMap(previousEntries || []);
  const current = new Map((currentEntries || []).map((entry) => [entry.key, entry.sha256]));
  const added = [];
  const changed = [];
  const unchanged = [];
  const removed = [];

  for (const [key, hash] of current.entries()) {
    if (!previous.has(key)) added.push(key);
    else if (previous.get(key) === hash) unchanged.push(key);
    else changed.push(key);
  }
  for (const key of previous.keys()) {
    if (!current.has(key)) removed.push(key);
  }
  for (const list of [added, changed, unchanged, removed]) list.sort(compareText);
  return {
    summary: {added: added.length, changed: changed.length, unchanged: unchanged.length, removed: removed.length},
    added,
    changed,
    unchanged,
    removed,
  };
}

function validateSessionFingerprint(sessionFingerprint, providerProfileId, projectRevision) {
  if (!sessionFingerprint || typeof sessionFingerprint !== 'object') throw manifestError('SESSION_FINGERPRINT_REQUIRED');
  if (sessionFingerprint.active_provider_profile !== providerProfileId) {
    throw manifestError('PROVIDER_FINGERPRINT_PROFILE_MISMATCH');
  }
  if (sessionFingerprint.project_revision !== projectRevision) {
    throw manifestError('PROJECT_REVISION_MISMATCH');
  }
  if (sessionFingerprint.minecraft_version !== TARGET.minecraftVersion
    || String(sessionFingerprint.loader).toLowerCase() !== TARGET.loader
    || sessionFingerprint.java_version !== TARGET.javaVersion) {
    throw manifestError('SESSION_TARGET_MISMATCH');
  }
}

function createFingerprints(sessionFingerprint) {
  const physicalProviders = (Array.isArray(sessionFingerprint.physical_providers) ? sessionFingerprint.physical_providers : [])
    .map((entry) => ({modId: entry.modId, modVersion: entry.modVersion}))
    .sort((a, b) => compareText(`${a.modId}:${a.modVersion}`, `${b.modId}:${b.modVersion}`));
  const installedExtensions = (Array.isArray(sessionFingerprint.installed_extensions) ? sessionFingerprint.installed_extensions : [])
    .map((entry) => ({pluginId: entry.pluginId, pluginVersion: entry.pluginVersion}))
    .sort((a, b) => compareText(`${a.pluginId}:${a.pluginVersion}`, `${b.pluginId}:${b.pluginVersion}`));
  return {
    providerFingerprint: {
      activeProviderProfile: sessionFingerprint.active_provider_profile,
      physicalProviders,
    },
    extensionFingerprint: {
      blockbenchVersion: sessionFingerprint.blockbench_version,
      installedExtensions,
    },
  };
}

function finalityBlockers({structuralQa, visualQa, captureEvidence, sourceArtifacts, staging, exportArtifacts, runtimeQa, handoffDestinations}) {
  const blockers = [];
  if (structuralQa.status !== 'PASS') blockers.push('STRUCTURAL_QA_NOT_PASS');
  if (visualQa.status !== 'PASS' || !visualQa.evidenceId) blockers.push('VISUAL_QA_NOT_PASS');
  if (!captureEvidence.length) blockers.push('CAPTURE_EVIDENCE_MISSING');
  if (!sourceArtifacts.length || sourceArtifacts.some((entry) => entry.preserve !== true)) blockers.push('SOURCE_PRESERVATION_INCOMPLETE');
  if (!['VALIDATED', 'PROMOTED'].includes(staging.state)) blockers.push('STAGING_NOT_VALIDATED');
  if (!exportArtifacts.length) blockers.push('EXPORT_OUTPUTS_MISSING');
  if (runtimeQa.status !== 'PASS' || !runtimeQa.evidenceId) blockers.push('RUNTIME_QA_NOT_PASS');
  if (!handoffDestinations.length) blockers.push('HANDOFF_DESTINATION_MISSING');
  return blockers;
}

function createUnifiedQaExportManifest(input = {}) {
  if (!input.project || typeof input.project !== 'object') throw manifestError('PROJECT_REQUIRED');
  if (!input.projectSnapshot || typeof input.projectSnapshot !== 'object') throw manifestError('PROJECT_SNAPSHOT_REQUIRED');
  const projectRevision = requiredString(input.projectSnapshot.projectRevision, 'PROJECT_REVISION_REQUIRED');
  const providerProfileId = requiredString(input.providerProfileId, 'PROVIDER_PROFILE_REQUIRED');
  const providerProfile = getProviderProfile(providerProfileId);
  if (!providerProfile) throw manifestError('UNKNOWN_PROVIDER_PROFILE', providerProfileId);
  validateSessionFingerprint(input.sessionFingerprint, providerProfileId, projectRevision);

  const structuralSummary = validateProject(input.project);
  const structuralQa = {status: structuralSummary.errors.length ? 'FAIL' : 'PASS', summary: structuralSummary};
  const report = createDeterministicReport(input.project);
  const {providerFingerprint, extensionFingerprint} = createFingerprints(input.sessionFingerprint);
  const sourceArtifacts = normalizeSourceArtifacts(input.sourceArtifacts || []);
  const captureEvidence = normalizeCaptureEvidence(input.captureEvidence || []);
  const visualQa = normalizeEvidence(input.visualQa || {status: 'PENDING'}, ['PASS', 'FAIL', 'PENDING'], 'VISUAL_QA_INVALID');

  const roots = normalizeRoots(input.exportPlan?.roots);
  const rootsById = rootMap(roots);
  const staging = normalizeStaging(input.exportPlan?.staging, rootsById);
  const exportArtifacts = normalizeExportArtifacts(input.exportPlan?.outputs || [], rootsById);
  const semanticDiff = createSemanticDiff(input.previousExportArtifacts || [], exportArtifacts);
  const runtimeTarget = normalizeRuntimeTarget(input.runtimeTarget);
  const runtimeQa = normalizeEvidence(input.runtimeQa || {status: 'UNPROVEN'}, ['PASS', 'FAIL', 'UNPROVEN', 'PENDING'], 'RUNTIME_QA_INVALID');
  const handoffDestinations = normalizeHandoffs(input.handoffDestinations || [], rootsById);

  const blockers = finalityBlockers({
    structuralQa,
    visualQa,
    captureEvidence,
    sourceArtifacts,
    staging,
    exportArtifacts,
    runtimeQa,
    handoffDestinations,
  });

  const manifest = {
    schema: 'minecraft-mod-factory/unified-qa-export-manifest@1',
    projectRevision,
    providerProfile,
    providerFingerprint,
    extensionFingerprint,
    structuralQa,
    visualQa,
    captureEvidence,
    sourceArtifacts,
    sourceHashes: sourceArtifacts.map((entry) => ({kind: entry.kind, path: entry.path, sha256: entry.sha256})),
    report,
    exportRoots: roots,
    staging,
    exportArtifacts,
    semanticDiff,
    runtimeTarget,
    runtimeQa,
    handoffDestinations,
    finality: {status: blockers.length ? 'PENDING' : 'FINAL', blockers},
    runtimeValidated: runtimeQa.status === 'PASS' && !!runtimeQa.evidenceId,
    f4I6Evidence: false,
    implicitProviderConversion: false,
  };
  return deepFreeze(manifest);
}

module.exports = {
  UNIFIED_QA_EXPORT_TARGET: TARGET,
  sha256ArtifactContent: sha256,
  createSemanticDiff,
  createUnifiedQaExportManifest,
};
