'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

const validator = require('./validate_base_safe.js');

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function canonical() {
  return validator.loadPreset();
}

function codes(errors) {
  return new Set(errors.map((error) => error.code));
}

test('canonical Base Safe preset passes fail-closed validation', () => {
  assert.deepEqual(validator.validatePreset(canonical()), []);
});

test('Base Safe contains the exact audited third-party extension set and toolkit-first order', () => {
  const preset = canonical();
  assert.deepEqual(preset.extensions.map((entry) => entry.pluginId), Object.keys(validator.EXPECTED_EXTENSIONS));
  assert.deepEqual(preset.installationOrder, validator.EXPECTED_ORDER);
});

test('duplicate extension ids fail closed', () => {
  const preset = canonical();
  preset.extensions[1].pluginId = preset.extensions[0].pluginId;
  assert.ok(codes(validator.validatePreset(preset)).has('DUPLICATE_EXTENSION_ID'));
});

test('provider-specific extensions are rejected from Base Safe', () => {
  const preset = canonical();
  preset.extensions[0] = {
    ...preset.extensions[0],
    pluginId: 'geckolib',
    title: 'GeckoLib Models & Animations',
    version: '4.2.5',
    minBlockbenchVersion: '5.0.0',
    sourcePath: 'plugins/geckolib.js',
  };
  const resultCodes = codes(validator.validatePreset(preset));
  assert.ok(resultCodes.has('UNEXPECTED_EXTENSION') || resultCodes.has('PROVIDER_EXTENSION_IN_BASE_SAFE'));
});

test('catalog version drift is rejected until explicitly re-audited', () => {
  const preset = canonical();
  preset.extensions.find((entry) => entry.pluginId === 'brush_tuna').version = '1.0.7';
  assert.ok(codes(validator.validatePreset(preset)).has('EXTENSION_METADATA_MISMATCH'));
});

test('extensions without upstream min_version remain smoke-required instead of receiving invented compatibility', () => {
  const preset = canonical();
  const missingTexture = preset.extensions.find((entry) => entry.pluginId === 'missing_texture_highlighter');
  const codeView = preset.extensions.find((entry) => entry.pluginId === 'code_view');
  assert.equal(missingTexture.minBlockbenchVersion, null);
  assert.equal(missingTexture.compatibilityMode, 'SMOKE_REQUIRED_NO_MIN_VERSION');
  assert.equal(codeView.minBlockbenchVersion, null);
  assert.equal(codeView.compatibilityMode, 'SMOKE_REQUIRED_NO_MIN_VERSION');

  codeView.compatibilityMode = 'MIN_VERSION_AND_SMOKE';
  assert.ok(codes(validator.validatePreset(preset)).has('COMPATIBILITY_MODE_MISMATCH'));
});

test('automatic installation and MCP access are rejected', () => {
  const preset = canonical();
  preset.humanInstallationOnly = false;
  preset.extensions[0].installation = 'AUTOMATIC';
  preset.extensions[0].mcpPolicy = 'ALLOWLIST';
  const resultCodes = codes(validator.validatePreset(preset));
  assert.ok(resultCodes.has('AUTOMATED_INSTALLATION_ALLOWED'));
  assert.ok(resultCodes.has('AUTOMATED_EXTENSION_INSTALLATION'));
  assert.ok(resultCodes.has('EXTENSION_MCP_ALLOWED'));
});

test('static minimum-version gates reject a Blockbench target below a plugin requirement', () => {
  const preset = canonical();
  preset.targetBlockbenchVersion = '5.1.3';
  const resultCodes = codes(validator.validatePreset(preset));
  assert.ok(resultCodes.has('UNEXPECTED_BLOCKBENCH_TARGET'));
  assert.ok(resultCodes.has('BLOCKBENCH_VERSION_INCOMPATIBLE'));
});

test('schema encodes the same provider-neutral and human-only invariants', () => {
  const schemaPath = path.join(__dirname, 'preset.schema.json');
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  assert.equal(schema.properties.presetId.const, 'base_safe');
  assert.equal(schema.properties.providerExtensionsAllowed.const, false);
  assert.equal(schema.properties.humanInstallationOnly.const, true);
  assert.equal(schema.properties.toolkit.properties.pluginId.const, 'rpg_asset_toolkit');
  assert.equal(schema.$defs.extension.properties.installation.const, 'HUMAN_ONLY');
  assert.equal(schema.$defs.extension.properties.mcpPolicy.const, 'NEVER');
  assert.equal(schema.properties.extensions.minItems, 11);
  assert.equal(schema.properties.extensions.maxItems, 11);
});

test('official catalog pin is immutable until an explicit audit updates validator and preset together', () => {
  const preset = canonical();
  preset.catalog.commit = '0000000000000000000000000000000000000000';
  assert.ok(codes(validator.validatePreset(preset)).has('CATALOG_PIN_MISMATCH'));
});
