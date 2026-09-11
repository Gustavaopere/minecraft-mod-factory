'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const azurelib3 = require('./core/provider-adapter/azurelib3_adapter.js');

const GOLDEN_ROOT = path.join(__dirname, '../../../golden-samples/model-asset/provider-regression/azurelib3');

function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(GOLDEN_ROOT, name), 'utf8'));
}

test('PR7 AzureLib Golden regression remains explicitly reference-only and cannot satisfy F4/I6 evidence', () => {
  const manifest = readJson('REFERENCE-EVIDENCE.json');
  assert.deepEqual(manifest.authority, azurelib3.AZURELIB3_AUTHORITY);
  assert.equal(manifest.classification, 'REFERENCE_ONLY');
  assert.equal(manifest.sourceNativeBbmodel, false);
  assert.equal(manifest.exporterProduced, false);
  assert.equal(manifest.runtimeValidated, false);
  assert.equal(manifest.f4I6Evidence, false);
  assert.equal(manifest.runtimeEvidence, 'UNPROVEN');
});

test('PR7 AzureLib Golden geometry exercises an audited AzureLib 3.1.11 runtime format', () => {
  const result = azurelib3.validateAzureLib3GeoDocument(readJson('factory-test.geo.json'));
  assert.equal(result.ok, true);
  assert.equal(result.formatVersion, '1.21.0');
  assert.equal(result.geometryCount, 1);
  assert.equal(result.boneCount, 2);
});

test('PR7 AzureLib Golden animation exercises custom easing awareness and all three effect channels', () => {
  const result = azurelib3.validateAzureLib3AnimationDocument(readJson('factory-test.animation.json'));
  assert.equal(result.ok, true);
  assert.equal(result.animationCount, 1);
  assert.equal(result.includeCount, 0);
  assert.deepEqual(result.effectCounts, {sound: 1, particle: 1, timeline: 1});
});
