'use strict';

const fs = require('node:fs');
const path = require('node:path');
const providerExtensions = require('../asset-toolkit/core/extension-registry/extension_registry.js');

const ROOT = __dirname;
const PRESET_PATH = path.join(ROOT, 'base-safe.json');

const EXPECTED_CATALOG = Object.freeze({
  repository: 'JannisX11/blockbench-plugins',
  commit: 'a33b2d88621cffc119f8e3d94795a2ec350c7290',
  catalogPath: 'plugins.json',
});

const EXPECTED_EXTENSIONS = Object.freeze({
  asset_browser: Object.freeze({title: 'Asset Browser', version: '1.2.2', minBlockbenchVersion: '5.0.0', variant: 'desktop', sourcePath: 'plugins/asset_browser/asset_browser.js'}),
  reference_models: Object.freeze({title: 'Reference Models', version: '1.1.0', minBlockbenchVersion: '5.0.0', variant: 'desktop', sourcePath: 'plugins/reference_models/reference_models.js'}),
  bone_view: Object.freeze({title: 'Bone View', version: '1.0.0', minBlockbenchVersion: '4.12.6', variant: 'both', sourcePath: 'plugins/bone_view/bone_view.js'}),
  cameras: Object.freeze({title: 'Cameras', version: '1.2.2', minBlockbenchVersion: '4.3.0', variant: 'both', sourcePath: 'plugins/cameras.js'}),
  resource_pack_utilities: Object.freeze({title: 'Resource Pack Utilities', version: '1.10.0', minBlockbenchVersion: '5.0.2', variant: 'desktop', sourcePath: 'plugins/resource_pack_utilities/resource_pack_utilities.js'}),
  uv_locker: Object.freeze({title: 'UV Locker', version: '1.0.0', minBlockbenchVersion: '5.0.0', variant: 'both', sourcePath: 'plugins/uv_locker/uv_locker.js'}),
  missing_texture_highlighter: Object.freeze({title: 'Missing Texture Highlighter', version: '0.1.1', minBlockbenchVersion: null, variant: 'both', sourcePath: 'plugins/missing_texture_highlighter.js'}),
  grayscale_preview: Object.freeze({title: 'Grayscale Preview', version: '1.0.0', minBlockbenchVersion: '4.3.0', variant: 'both', sourcePath: 'plugins/grayscale_preview.js'}),
  code_view: Object.freeze({title: 'Code View', version: '1.0.1', minBlockbenchVersion: null, variant: 'both', sourcePath: 'plugins/code_view.js'}),
  brush_tuna: Object.freeze({title: 'Brush Tuna', version: '1.0.6', minBlockbenchVersion: '5.1.4', variant: 'both', sourcePath: 'plugins/brush_tuna/brush_tuna.js'}),
  colour_gradient_generator: Object.freeze({title: 'Colour Gradient Generator', version: '3.0.0', minBlockbenchVersion: '5.0.0', variant: 'both', sourcePath: 'plugins/colour_gradient_generator/colour_gradient_generator.js'}),
});

const EXPECTED_ORDER = Object.freeze([
  'rpg_asset_toolkit',
  ...Object.keys(EXPECTED_EXTENSIONS),
]);

function numericVersion(value) {
  if (typeof value !== 'string' || !/^\d+(?:\.\d+)*$/.test(value.trim())) return null;
  return value.trim().split('.').map((part) => Number.parseInt(part, 10));
}

function compareVersions(leftValue, rightValue) {
  const left = numericVersion(leftValue);
  const right = numericVersion(rightValue);
  if (!left || !right) return null;
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    const delta = (left[index] || 0) - (right[index] || 0);
    if (delta !== 0) return delta < 0 ? -1 : 1;
  }
  return 0;
}

function validatePreset(preset) {
  const errors = [];
  const fail = (code, message) => errors.push({code, message});

  if (!preset || typeof preset !== 'object' || Array.isArray(preset)) {
    return [{code: 'INVALID_PRESET', message: 'Preset must be an object.'}];
  }

  if (preset.presetId !== 'base_safe') fail('INVALID_PRESET_ID', 'presetId must be base_safe.');
  if (preset.targetBlockbenchVersion !== '5.1.6') fail('UNEXPECTED_BLOCKBENCH_TARGET', 'Base Safe is pinned to the physically observed Blockbench 5.1.6 target.');
  if (preset.purpose !== 'authoring_and_qa_without_provider_specific_extensions') fail('INVALID_PURPOSE', 'Base Safe purpose must remain provider-neutral authoring and QA.');
  if (preset.providerExtensionsAllowed !== false) fail('PROVIDER_EXTENSIONS_ALLOWED', 'Base Safe must fail closed on provider-specific extensions.');
  if (preset.humanInstallationOnly !== true) fail('AUTOMATED_INSTALLATION_ALLOWED', 'Extension installation must remain human-only.');

  const catalog = preset.catalog || {};
  for (const [key, expected] of Object.entries(EXPECTED_CATALOG)) {
    if (catalog[key] !== expected) fail('CATALOG_PIN_MISMATCH', `catalog.${key} must equal ${expected}.`);
  }
  if (typeof catalog.auditedAt !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(catalog.auditedAt)) {
    fail('INVALID_AUDIT_DATE', 'catalog.auditedAt must be YYYY-MM-DD.');
  }

  const toolkit = preset.toolkit || {};
  if (toolkit.pluginId !== 'rpg_asset_toolkit') fail('TOOLKIT_ID_MISMATCH', 'Toolkit pluginId must be rpg_asset_toolkit.');
  if (toolkit.sourceBundle !== '../asset-toolkit/asset_toolkit.js') fail('TOOLKIT_SOURCE_MISMATCH', 'Toolkit canonical source bundle path changed unexpectedly.');
  if (toolkit.installArtifact !== '../asset-toolkit/rpg_asset_toolkit.js') fail('TOOLKIT_INSTALL_ARTIFACT_MISMATCH', 'Toolkit local install artifact path changed unexpectedly.');
  if (toolkit.installArtifactGeneratedOnDemand !== true) fail('TOOLKIT_ARTIFACT_NOT_GENERATED', 'Toolkit install artifact must remain generated on demand.');
  if (typeof toolkit.sourceCommit !== 'string' || !/^[0-9a-f]{40}$/.test(toolkit.sourceCommit)) fail('INVALID_TOOLKIT_SOURCE_COMMIT', 'Toolkit sourceCommit must be a full Git SHA.');
  if (toolkit.installation !== 'HUMAN_ONLY') fail('TOOLKIT_AUTOMATED_INSTALLATION', 'Toolkit installation must remain human-only.');
  if (toolkit.mcpPolicy !== 'READ_ONLY_BRIDGE_ONLY') fail('TOOLKIT_MCP_POLICY_MISMATCH', 'Toolkit MCP surface must remain read-only bridge only.');
  if (toolkit.rollback !== 'REMOVE_LOCAL_SIDELOAD_AND_RESTART_BLOCKBENCH') fail('TOOLKIT_ROLLBACK_MISSING', 'Toolkit rollback contract is required.');
  if (toolkit.smokeRequired !== true) fail('TOOLKIT_SMOKE_NOT_REQUIRED', 'Toolkit smoke must remain mandatory.');

  if (!Array.isArray(preset.extensions)) {
    fail('EXTENSIONS_NOT_ARRAY', 'extensions must be an array.');
  } else {
    const seen = new Set();
    const expectedIds = Object.keys(EXPECTED_EXTENSIONS);
    if (preset.extensions.length !== expectedIds.length) fail('EXTENSION_COUNT_MISMATCH', `Base Safe requires exactly ${expectedIds.length} third-party extensions.`);

    const providerIds = new Set(Object.keys(providerExtensions.EXTENSION_CATALOG || {}));

    for (const extension of preset.extensions) {
      if (!extension || typeof extension !== 'object') {
        fail('INVALID_EXTENSION', 'Each extension entry must be an object.');
        continue;
      }
      const id = extension.pluginId;
      if (seen.has(id)) fail('DUPLICATE_EXTENSION_ID', `Duplicate extension ${id}.`);
      seen.add(id);

      const expected = EXPECTED_EXTENSIONS[id];
      if (!expected) {
        fail('UNEXPECTED_EXTENSION', `Unexpected Base Safe extension ${id}.`);
        continue;
      }
      if (providerIds.has(id)) fail('PROVIDER_EXTENSION_IN_BASE_SAFE', `${id} belongs to the provider extension registry and cannot be in Base Safe.`);

      for (const key of ['title', 'version', 'minBlockbenchVersion', 'variant', 'sourcePath']) {
        if (extension[key] !== expected[key]) fail('EXTENSION_METADATA_MISMATCH', `${id}.${key} must equal ${String(expected[key])}.`);
      }

      const expectedMode = expected.minBlockbenchVersion === null ? 'SMOKE_REQUIRED_NO_MIN_VERSION' : 'MIN_VERSION_AND_SMOKE';
      if (extension.compatibilityMode !== expectedMode) fail('COMPATIBILITY_MODE_MISMATCH', `${id} must use ${expectedMode}.`);
      if (extension.installation !== 'HUMAN_ONLY') fail('AUTOMATED_EXTENSION_INSTALLATION', `${id} must remain HUMAN_ONLY.`);
      if (extension.mcpPolicy !== 'NEVER') fail('EXTENSION_MCP_ALLOWED', `${id} must remain unavailable to MCP installation/execution policy.`);
      if (!['THIRD_PARTY_LOCAL_PLUGIN', 'THIRD_PARTY_LOCAL_PLUGIN_FILESYSTEM'].includes(extension.risk)) fail('INVALID_EXTENSION_RISK', `${id} has an invalid risk classification.`);
      if (extension.rollback !== 'REMOVE_VIA_BLOCKBENCH_PLUGIN_DIALOG') fail('ROLLBACK_MISSING', `${id} must declare the Blockbench removal rollback.`);
      if (extension.smokeRequired !== true) fail('SMOKE_NOT_REQUIRED', `${id} must require a post-install smoke.`);

      if (expected.minBlockbenchVersion !== null) {
        const comparison = compareVersions(preset.targetBlockbenchVersion, expected.minBlockbenchVersion);
        if (comparison === null || comparison < 0) fail('BLOCKBENCH_VERSION_INCOMPATIBLE', `${id} requires Blockbench >= ${expected.minBlockbenchVersion}.`);
      }
    }

    for (const expectedId of expectedIds) {
      if (!seen.has(expectedId)) fail('MISSING_EXTENSION', `Missing required Base Safe extension ${expectedId}.`);
    }
  }

  if (!Array.isArray(preset.installationOrder) || preset.installationOrder.length !== EXPECTED_ORDER.length) {
    fail('INSTALLATION_ORDER_INVALID', `installationOrder must contain exactly ${EXPECTED_ORDER.length} entries.`);
  } else if (preset.installationOrder.some((id, index) => id !== EXPECTED_ORDER[index])) {
    fail('INSTALLATION_ORDER_MISMATCH', 'installationOrder must preserve the audited Base Safe order with the toolkit first.');
  }

  return errors;
}

function loadPreset(filePath = PRESET_PATH) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function main() {
  const preset = loadPreset();
  const errors = validatePreset(preset);
  if (errors.length) {
    for (const error of errors) console.error(`${error.code}: ${error.message}`);
    process.exitCode = 1;
    return;
  }
  console.log(`Base Safe PASS: ${preset.extensions.length} third-party extensions + ${preset.toolkit.pluginId} for Blockbench ${preset.targetBlockbenchVersion}.`);
}

if (require.main === module) main();

module.exports = {
  EXPECTED_CATALOG,
  EXPECTED_EXTENSIONS,
  EXPECTED_ORDER,
  compareVersions,
  loadPreset,
  validatePreset,
};
