'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');
const {loadEvidence, validateRealHandoffEvidence} = require('./validate_real_handoff_evidence.js');

const cloneJson = (value) => JSON.parse(JSON.stringify(value));
const cloneEvidence = () => {
  const source = loadEvidence();
  return {
    manifest: cloneJson(source.manifest),
    model: {
      ...source.model,
      declaration: cloneJson(source.model.declaration),
      expectedDeclaration: cloneJson(source.model.expectedDeclaration),
      aliasDeclaration: cloneJson(source.model.aliasDeclaration),
      rawBuffer: Buffer.from(source.model.rawBuffer),
      rawJson: cloneJson(source.model.rawJson),
      expectedJson: cloneJson(source.model.expectedJson),
      aliasBuffer: Buffer.from(source.model.aliasBuffer),
      aliasJson: cloneJson(source.model.aliasJson),
    },
    animation: {
      ...source.animation,
      declaration: cloneJson(source.animation.declaration),
      expectedDeclaration: cloneJson(source.animation.expectedDeclaration),
      aliasDeclaration: cloneJson(source.animation.aliasDeclaration),
      rawBuffer: Buffer.from(source.animation.rawBuffer),
      rawJson: cloneJson(source.animation.rawJson),
      expectedJson: cloneJson(source.animation.expectedJson),
      aliasBuffer: Buffer.from(source.animation.aliasBuffer),
      aliasJson: cloneJson(source.animation.aliasJson),
    },
  };
};

test('real GeckoLib handoff satisfies the completed authoring/export/reopen/runtime contract', () => {
  const result = validateRealHandoffEvidence();
  assert.equal(result.ok, true);
  assert.equal(result.exporterProduced, true);
  assert.equal(result.reopenValidated, true);
  assert.equal(result.runtimeValidated, true);
  assert.equal(result.f4I6Evidence, true);
  assert.equal(result.runtimeEvidence.classification, 'PASS');
  assert.equal(result.runtimeEvidence.workflowRunId, 34710808440);
  assert.equal(result.runtimeEvidence.jobId, 103599143647);
});

test('fails closed when a raw exporter hash drifts', () => {
  const evidence = cloneEvidence();
  evidence.model.declaration.sha256 = '0'.repeat(64);
  assert.throws(() => validateRealHandoffEvidence(evidence), /ACTUAL_EXPORT_HASH_DRIFT/);
});

test('fails closed when actual export diverges from reconciled expected contract', () => {
  const evidence = cloneEvidence();
  evidence.model.expectedJson['minecraft:geometry'][0].description.visible_bounds_width = 99;
  assert.throws(() => validateRealHandoffEvidence(evidence), /EXPORTER_CONTRACT_DIVERGENCE/);
});

test('fails closed when canonical alias bytes differ from raw exporter bytes', () => {
  const evidence = cloneEvidence();
  evidence.animation.aliasBuffer = Buffer.from('{}\n');
  assert.throws(() => validateRealHandoffEvidence(evidence), /CANONICAL_ALIAS_BYTE_DRIFT/);
});

test('fails closed when reopen is claimed without complete manual playback evidence', () => {
  const evidence = cloneEvidence();
  evidence.manifest.manualEvidence.walkPlaybackValidated = false;
  assert.throws(() => validateRealHandoffEvidence(evidence), /INVALID_MANUAL_EVIDENCE/);
});

test('fails closed when reopen evidence is revoked after being physically proven', () => {
  const evidence = cloneEvidence();
  evidence.manifest.realHandoff.reopenValidated = false;
  assert.throws(() => validateRealHandoffEvidence(evidence), /INVALID_REAL_HANDOFF_FLAGS/);
});

test('fails closed when F4/I6 is claimed without runtime validation', () => {
  const evidence = cloneEvidence();
  evidence.manifest.realHandoff.runtimeValidated = false;
  assert.throws(() => validateRealHandoffEvidence(evidence), /INVALID_REAL_HANDOFF_FLAGS/);
});

test('fails closed when durable runtime provenance drifts', () => {
  const evidence = cloneEvidence();
  evidence.manifest.realHandoff.runtimeEvidence.workflowRunId = 1;
  assert.throws(() => validateRealHandoffEvidence(evidence), /INVALID_RUNTIME_PROVENANCE/);
});

test('fails closed when target-exact runtime evidence drifts', () => {
  const evidence = cloneEvidence();
  evidence.manifest.realHandoff.runtimeEvidence.target.neoforge = '21.1.249';
  assert.throws(() => validateRealHandoffEvidence(evidence), /INVALID_RUNTIME_TARGET/);
});

test('fails closed when live-client animation proof is revoked', () => {
  const evidence = cloneEvidence();
  evidence.manifest.realHandoff.runtimeEvidence.client.animation_motion_observed = false;
  assert.throws(() => validateRealHandoffEvidence(evidence), /INVALID_RUNTIME_CLIENT_EVIDENCE/);
});

test('fails closed when the observed GeckoLib coordinate transform drifts', () => {
  const evidence = cloneEvidence();
  evidence.animation.rawJson.animations['animation.golden_sample_mob.walk'].bones.left_leg.rotation['0.0'].vector = [25, 0, 0];
  evidence.animation.expectedJson = cloneJson(evidence.animation.rawJson);
  evidence.animation.aliasJson = cloneJson(evidence.animation.rawJson);
  assert.throws(() => validateRealHandoffEvidence(evidence), /REAL_ANIMATION_COORDINATE_DRIFT/);
});
