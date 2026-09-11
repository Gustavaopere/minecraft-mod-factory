'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const geckolib4 = require('./core/provider-adapter/geckolib4_adapter.js');

const GOLDEN_ROOT = path.join(__dirname, '../../../golden-samples/model-asset/provider-regression/geckolib4');

function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(GOLDEN_ROOT, name), 'utf8'));
}

test('PR6 GeckoLib Golden regression remains explicitly reference-only and cannot satisfy F4/I6 evidence', () => {
  const manifest = readJson('REFERENCE-EVIDENCE.json');
  assert.deepEqual(manifest.authority, geckolib4.GECKOLIB4_AUTHORITY);
  assert.equal(manifest.classification, 'REFERENCE_ONLY');
  assert.equal(manifest.sourceNativeBbmodel, false);
  assert.equal(manifest.exporterProduced, false);
  assert.equal(manifest.runtimeValidated, false);
  assert.equal(manifest.f4I6Evidence, false);
  assert.equal(manifest.runtimeEvidence, 'UNPROVEN');
});

test('PR6 GeckoLib Golden geometry exercises audited runtime format and both locator representations', () => {
  const result = geckolib4.validateGeckoLib4GeoDocument(readJson('factory-test.geo.json'));
  assert.equal(result.ok, true);
  assert.equal(result.formatVersion, '1.12.0');
  assert.equal(result.geometryCount, 1);
  assert.equal(result.locatorCount, 2);
});

test('PR6 GeckoLib Golden animation exercises audited transforms and all three effect channels', () => {
  const result = geckolib4.validateGeckoLib4AnimationDocument(readJson('factory-test.animation.json'));
  assert.equal(result.ok, true);
  assert.equal(result.animationCount, 1);
  assert.deepEqual(result.effectCounts, {sound: 1, particle: 1, timeline: 1});
});
