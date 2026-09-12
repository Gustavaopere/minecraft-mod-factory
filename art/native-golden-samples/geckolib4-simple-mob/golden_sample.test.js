'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {loadSample, validateSample} = require('./validate_golden_sample.js');
const clone = (value) => JSON.parse(JSON.stringify(value));

test('native GeckoLib Golden Sample satisfies the validated real handoff contract', () => {
  const result = validateSample();
  assert.equal(result.ok, true);
  assert.equal(result.native.cubeCount, 4);
  assert.equal(result.native.locatorCount, 1);
  assert.equal(result.native.animationCount, 2);
  assert.equal(result.texture.width, 32);
  assert.equal(result.texture.height, 32);
  assert.equal(result.exportPlan.preserveSource, true);
});

test('fails closed when native source format drifts away from GeckoLib bbmodel', () => {
  const sample = loadSample(); sample.bbmodel = clone(sample.bbmodel); sample.bbmodel.meta.model_format = 'free';
  assert.throws(() => validateSample(sample), /INVALID_BBMODEL_MODEL_FORMAT/);
});

test('fails closed when the embedded texture diverges from the canonical PNG', () => {
  const sample = loadSample(); sample.bbmodel = clone(sample.bbmodel); sample.bbmodel.textures[0].source = 'data:image/png;base64,iVBORw0KGgo=';
  assert.throws(() => validateSample(sample), /BBMODEL_TEXTURE_DIVERGENCE/);
});

test('fails closed when provider plugin pin drifts', () => {
  const sample = loadSample(); sample.manifest = clone(sample.manifest); sample.manifest.provider.blockbenchPluginVersion = '0.0.0';
  assert.throws(() => validateSample(sample), /PROVIDER_AUTHORITY_DRIFT/);
});

test('fails closed on incomplete I6 completion claim', () => {
  const sample = loadSample(); sample.manifest = clone(sample.manifest); sample.manifest.realHandoff.runtimeValidated = false;
  assert.throws(() => validateSample(sample), /PREMATURE_I6_EVIDENCE/);
});

test('fails closed when exporter evidence is claimed without actual outputs', () => {
  const sample = loadSample();
  sample.manifest = clone(sample.manifest);
  sample.manifest.realHandoff.exporterProduced = true;
  sample.actualGeo = null;
  sample.actualAnimation = null;
  assert.throws(() => validateSample(sample), /MISSING_EXPORTER_EVIDENCE/);
});

test('fails closed when actual outputs exist but exporter evidence is revoked', () => {
  const sample = loadSample();
  sample.manifest = clone(sample.manifest);
  sample.manifest.realHandoff.exporterProduced = false;
  assert.throws(() => validateSample(sample), /PREMATURE_I6_EVIDENCE|UNCLASSIFIED_ACTUAL_OUTPUT/);
});
