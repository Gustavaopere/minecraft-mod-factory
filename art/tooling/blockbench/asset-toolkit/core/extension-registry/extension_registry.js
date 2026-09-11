'use strict';

const EXTENSION_STATES = Object.freeze([
  'REQUIRED_PROFILE', 'PREFERRED', 'OPTIONAL', 'EXPERIMENTAL', 'DEV_ONLY',
  'HUMAN_ONLY', 'AUDIT_REQUIRED', 'BLOCKED_LEGACY', 'INCOMPATIBLE_EDITOR',
  'LOADER_MISMATCH', 'PROVIDER_ABSENT', 'NOT_RUNTIME_AUTHORITY', 'DISABLED_BY_DEFAULT',
]);

const BLOCKING_CLASSIFICATIONS = new Set([
  'HUMAN_ONLY', 'AUDIT_REQUIRED', 'BLOCKED_LEGACY', 'INCOMPATIBLE_EDITOR',
  'LOADER_MISMATCH', 'PROVIDER_ABSENT',
]);

const EXTENSION_CATALOG = Object.freeze({
  geckolib: Object.freeze({
    pluginId: 'geckolib',
    title: 'GeckoLib Models & Animations',
    pluginVersion: '4.2.5',
    classification: 'REQUIRED_PROFILE',
    blockbenchCompatibility: Object.freeze({minInclusive: '5.0.0', maxExclusive: '6.0.0'}),
    mcpPolicy: 'ALLOWLIST',
    providerFamily: 'geckolib4',
  }),
  animation_utils: Object.freeze({
    pluginId: 'animation_utils',
    title: 'GeckoLib Animation Utils',
    pluginVersion: '4.1.3',
    classification: 'BLOCKED_LEGACY',
    mcpPolicy: 'NEVER',
    providerFamily: 'geckolib4',
  }),
  azurelib_utils: Object.freeze({
    pluginId: 'azurelib_utils',
    title: 'AzureLib Animator',
    pluginVersion: '2.1.5',
    classification: 'REQUIRED_PROFILE',
    blockbenchCompatibility: Object.freeze({auditedExact: Object.freeze(['5.1.6'])}),
    mcpPolicy: 'ALLOWLIST',
    providerFamily: 'azurelib',
  }),
  animation_to_json: Object.freeze({
    pluginId: 'animation_to_json',
    title: 'Animation to JSON Converter',
    pluginVersion: '1.0.1',
    classification: 'AUDIT_REQUIRED',
    mcpPolicy: 'NEVER',
    providerFamily: 'neoforge_native_animation',
  }),
  easy_model_entities: Object.freeze({
    pluginId: 'easy_model_entities',
    title: 'Easy Model Entities',
    pluginVersion: '1.0.0',
    classification: 'REQUIRED_PROFILE',
    blockbenchCompatibility: Object.freeze({auditedExact: Object.freeze(['5.1.6'])}),
    mcpPolicy: 'ALLOWLIST',
    providerFamily: 'easy_model_entities',
  }),
  cem_template_loader: Object.freeze({
    pluginId: 'cem_template_loader',
    title: 'CEM Template Loader',
    pluginVersion: '9.2.0',
    classification: 'REQUIRED_PROFILE',
    blockbenchCompatibility: Object.freeze({minInclusive: '5.0.0'}),
    mcpPolicy: 'ALLOWLIST',
    providerFamily: 'emf_cem',
  }),
  emf_animation_addon: Object.freeze({
    pluginId: 'emf_animation_addon',
    title: 'EMF Animation Addon',
    pluginVersion: '1.0.5',
    classification: 'PREFERRED',
    blockbenchCompatibility: Object.freeze({minInclusive: '4.9.0'}),
    mcpPolicy: 'ALLOWLIST',
    providerFamily: 'emf_cem',
  }),
  animated_java: Object.freeze({
    pluginId: 'animated_java',
    title: 'Animated Java',
    pluginVersion: '1.10.2',
    classification: 'OPTIONAL',
    blockbenchCompatibility: Object.freeze({minInclusive: '5.1.4'}),
    mcpPolicy: 'ALLOWLIST',
    providerFamily: 'animated_java',
  }),
});

function numericVersion(value) {
  if (typeof value !== 'string' || !/^\d+(?:\.\d+)*$/.test(value.trim())) return null;
  return value.trim().split('.').map((part) => Number.parseInt(part, 10));
}

function compareNumericVersions(a, b) {
  const left = numericVersion(a);
  const right = numericVersion(b);
  if (!left || !right) return null;
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    const delta = (left[index] || 0) - (right[index] || 0);
    if (delta !== 0) return delta < 0 ? -1 : 1;
  }
  return 0;
}

function blockbenchCompatible(definition, blockbenchVersion) {
  const compatibility = definition && definition.blockbenchCompatibility;
  if (!compatibility) return true;
  if (typeof blockbenchVersion !== 'string' || !blockbenchVersion.trim()) return false;
  if (Array.isArray(compatibility.auditedExact)) return compatibility.auditedExact.includes(blockbenchVersion.trim());
  if (compatibility.minInclusive) {
    const comparison = compareNumericVersions(blockbenchVersion.trim(), compatibility.minInclusive);
    if (comparison === null || comparison < 0) return false;
  }
  if (compatibility.maxExclusive) {
    const comparison = compareNumericVersions(blockbenchVersion.trim(), compatibility.maxExclusive);
    if (comparison === null || comparison >= 0) return false;
  }
  return true;
}

function getExtensionDefinition(pluginId) {
  return typeof pluginId === 'string' ? EXTENSION_CATALOG[pluginId] || null : null;
}

function evaluateExtension(definition, session = {}) {
  if (!definition || typeof definition !== 'object' || typeof definition.pluginId !== 'string') {
    return {installed: false, compatible: false, versionMatch: false, mcpAllowed: false, reasons: ['INVALID_EXTENSION_DEFINITION']};
  }

  const reasons = [];
  const installedExtensions = Array.isArray(session.installedExtensions) ? session.installedExtensions : [];
  const installed = installedExtensions.find((entry) => entry && entry.pluginId === definition.pluginId) || null;
  const isInstalled = !!installed;
  if (!isInstalled) reasons.push('NOT_INSTALLED');

  const versionMatch = !!installed && typeof installed.pluginVersion === 'string'
    && installed.pluginVersion === definition.pluginVersion;
  if (isInstalled && !versionMatch) reasons.push('EXTENSION_VERSION_MISMATCH');

  const compatible = blockbenchCompatible(definition, session.blockbenchVersion);
  if (!compatible) reasons.push('BLOCKBENCH_VERSION_INCOMPATIBLE');

  const classificationBlocksMcp = BLOCKING_CLASSIFICATIONS.has(definition.classification) || definition.mcpPolicy === 'NEVER';
  if (classificationBlocksMcp) reasons.push('CLASSIFICATION_BLOCKS_MCP');

  const authorizedIds = Array.isArray(session.mcpAuthorizedExtensionIds) ? session.mcpAuthorizedExtensionIds : [];
  const authorized = authorizedIds.includes(definition.pluginId);
  if (!authorized) reasons.push('NOT_MCP_AUTHORIZED');

  const mcpAllowed = isInstalled && versionMatch && compatible && authorized
    && definition.mcpPolicy === 'ALLOWLIST' && !classificationBlocksMcp;

  return {installed: isInstalled, compatible, versionMatch, mcpAllowed, reasons: [...new Set(reasons)]};
}

module.exports = {
  EXTENSION_STATES,
  EXTENSION_CATALOG,
  getExtensionDefinition,
  evaluateExtension,
  compareNumericVersions,
};
