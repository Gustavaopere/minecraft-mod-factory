'use strict';

const {isPlainObject} = require('../common/contract_utils.js');

const PROFILE_ID = 'animated_java_display_entities';
const EXPORT_MODES = Object.freeze(['folder', 'zip', 'none']);
const EXPORT_MODE_SET = new Set(EXPORT_MODES);

const ANIMATED_JAVA_AUTHORITY = Object.freeze({
  providerFamily: 'animated_java',
  minecraftVersion: '1.21.1',
  pluginId: 'animated_java',
  pluginVersion: '1.10.2',
  pluginSource: 'Animated-Java/animated-java',
  pluginRef: 'a5fc548d2a53cc0887fa070db33ccfcef1cd3541',
  releaseAsset: 'animated_java.js',
  releaseAssetSha256: '81aadc4def796d97dab6642ad05b564b470ecadcaf455c8cc5826c9e24759672',
  blockbenchVersion: '5.1.6',
  blockbenchSource: 'JannisX11/blockbench',
  blockbenchRef: '794e964e966b6783b4e9b98ecbdda5152c0620cc',
  blockbenchMinimumVersion: '5.1.4',
  blueprintFormatId: 'animated-java:format/blueprint',
  blueprintCodecId: 'animated_java:codec/blueprint',
  sourceExtension: '.ajblueprint',
  exportModes: EXPORT_MODES,
  compilerRange: Object.freeze({minInclusive: '1.21.0', maxExclusive: '1.21.2'}),
});

const BLUEPRINT_FIELDS = new Set([
  'meta', 'blueprint_settings', 'resolution', 'elements', 'groups', 'outliner', 'textures',
  'animations', 'animation_controllers', 'animation_variable_placeholders', 'backgrounds',
  'collections',
]);
const META_FIELDS = new Set([
  'format', 'format_version', 'uuid', 'last_used_blueprint_id', 'box_uv', 'backup', 'save_location',
]);
const SETTINGS_FIELDS = new Set([
  'blueprint_id', 'show_render_box', 'auto_render_box', 'render_box', 'enable_plugin_mode',
  'resource_pack_export_mode', 'data_pack_export_mode', 'target_minecraft_version', 'display_item',
  'custom_model_data_offset', 'enable_advanced_resource_pack_settings', 'resource_pack',
  'enable_advanced_data_pack_settings', 'data_pack', 'on_summon_function', 'on_remove_function',
  'on_pre_tick_function', 'on_post_tick_function', 'interpolation_duration', 'teleportation_duration',
  'custom_rig_entity_tags', 'auto_update_rig_orientation', 'use_storage_for_animation',
  'use_entity_stacking', 'baked_animations', 'json_file',
]);

class AnimatedJavaContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'AnimatedJavaContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new AnimatedJavaContractError(code, message);
}

function rejectUnknownFields(value, allowed, code, context) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) fail(code, `${context}.${key} is outside the audited Animated Java 1.10.2 contract.`);
  }
}

function cloneAndFreeze(value, field = 'blueprint') {
  if (Array.isArray(value)) return Object.freeze(value.map((item, index) => cloneAndFreeze(item, `${field}[${index}]`)));
  if (isPlainObject(value)) {
    const output = {};
    for (const [key, item] of Object.entries(value)) output[key] = cloneAndFreeze(item, `${field}.${key}`);
    return Object.freeze(output);
  }
  if (value === null || value === undefined || ['string', 'number', 'boolean'].includes(typeof value)) return value;
  fail('INVALID_ANIMATED_JAVA_BLUEPRINT_VALUE', `${field} contains a value that cannot be preserved in audited JSON output.`);
}

function validateExportMode(value, field) {
  if (!EXPORT_MODE_SET.has(value)) {
    fail('INVALID_ANIMATED_JAVA_EXPORT_MODE', `${field} must be one of ${EXPORT_MODES.join(', ')}.`);
  }
  return value;
}

function parseBlueprintId(value) {
  if (typeof value !== 'string') fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'blueprintId must be a Minecraft resource location.');
  const separator = value.indexOf(':');
  if (separator <= 0 || separator === value.length - 1) {
    fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'blueprintId must include namespace:path.');
  }
  const namespace = value.slice(0, separator);
  const resourcePath = value.slice(separator + 1);
  if (!/^[a-z0-9_]+$/.test(namespace) || !/^[a-z0-9_/]+$/.test(resourcePath)) {
    fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'blueprintId must match the audited Animated Java lowercase resource-location grammar.');
  }
  if (namespace === 'minecraft') {
    fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'Animated Java blueprintId cannot use the minecraft namespace.');
  }
  if (namespace === 'animated_java' && resourcePath === 'global') {
    fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'animated_java:global is reserved by Animated Java.');
  }
  return Object.freeze({namespace, path: resourcePath});
}

function normalizeSourcePath(value) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('ANIMATED_JAVA_SOURCE_NOT_SAVED', 'Animated Java source project must be saved as .ajblueprint before handoff.');
  }
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith(ANIMATED_JAVA_AUTHORITY.sourceExtension)) {
    fail('ANIMATED_JAVA_SOURCE_NOT_SAVED', 'Animated Java source authority must remain a saved .ajblueprint file.');
  }
  return normalized;
}

function validateAnimatedJavaBlueprint(value) {
  if (!isPlainObject(value)) fail('INVALID_ANIMATED_JAVA_BLUEPRINT', 'Blueprint must be a plain object.');
  rejectUnknownFields(value, BLUEPRINT_FIELDS, 'INVALID_ANIMATED_JAVA_BLUEPRINT_FIELD', 'blueprint');
  if (!isPlainObject(value.meta)) fail('INVALID_ANIMATED_JAVA_BLUEPRINT_META', 'Blueprint meta is required.');
  rejectUnknownFields(value.meta, META_FIELDS, 'INVALID_ANIMATED_JAVA_BLUEPRINT_META_FIELD', 'meta');
  if (value.meta.format !== ANIMATED_JAVA_AUTHORITY.blueprintFormatId) {
    fail('INVALID_ANIMATED_JAVA_BLUEPRINT_FORMAT', `meta.format must be ${ANIMATED_JAVA_AUTHORITY.blueprintFormatId}.`);
  }
  if (value.meta.format_version !== undefined && value.meta.format_version !== ANIMATED_JAVA_AUTHORITY.pluginVersion) {
    fail('INVALID_ANIMATED_JAVA_BLUEPRINT_VERSION', `meta.format_version must be ${ANIMATED_JAVA_AUTHORITY.pluginVersion} for the audited PR11 handoff.`);
  }
  if (!isPlainObject(value.blueprint_settings)) {
    fail('INVALID_ANIMATED_JAVA_BLUEPRINT_SETTINGS', 'blueprint_settings are required for audited export.');
  }
  rejectUnknownFields(
    value.blueprint_settings,
    SETTINGS_FIELDS,
    'INVALID_ANIMATED_JAVA_BLUEPRINT_SETTING',
    'blueprint_settings',
  );
  parseBlueprintId(value.blueprint_settings.blueprint_id);
  if (value.blueprint_settings.target_minecraft_version !== ANIMATED_JAVA_AUTHORITY.minecraftVersion) {
    fail(
      'UNSUPPORTED_ANIMATED_JAVA_MINECRAFT_VERSION',
      `Factory PR11 is pinned to Minecraft ${ANIMATED_JAVA_AUTHORITY.minecraftVersion}.`,
    );
  }
  validateExportMode(value.blueprint_settings.resource_pack_export_mode, 'resource_pack_export_mode');
  validateExportMode(value.blueprint_settings.data_pack_export_mode, 'data_pack_export_mode');
  return cloneAndFreeze(value);
}

function requireExportPath(mode, value, field) {
  if (mode === 'none') return value ?? '';
  if (typeof value !== 'string' || value.length === 0) {
    fail('INVALID_ANIMATED_JAVA_EXPORT_PATH', `${field} is required when export mode is ${mode}.`);
  }
  return value.replace(/\\/g, '/');
}

function createAnimatedJavaExportPlan(input) {
  if (!isPlainObject(input)) fail('INVALID_ANIMATED_JAVA_EXPORT_PLAN', 'Export plan input must be a plain object.');
  const sourcePath = normalizeSourcePath(input.sourcePath);
  const parsed = parseBlueprintId(input.blueprintId);
  if (input.targetMinecraftVersion !== ANIMATED_JAVA_AUTHORITY.minecraftVersion) {
    fail(
      'UNSUPPORTED_ANIMATED_JAVA_MINECRAFT_VERSION',
      `Factory PR11 is pinned to Minecraft ${ANIMATED_JAVA_AUTHORITY.minecraftVersion}.`,
    );
  }
  const resourcePackExportMode = validateExportMode(input.resourcePackExportMode, 'resourcePackExportMode');
  const dataPackExportMode = validateExportMode(input.dataPackExportMode, 'dataPackExportMode');
  const resourcePackPath = requireExportPath(resourcePackExportMode, input.resourcePackPath, 'resourcePackPath');
  const dataPackPath = requireExportPath(dataPackExportMode, input.dataPackPath, 'dataPackPath');
  const modelExportRoot = `assets/${parsed.namespace}/models/blueprint/${parsed.path}`;
  const textureExportRoot = `assets/${parsed.namespace}/textures/blueprint/${parsed.path}`;

  return Object.freeze({
    profileId: PROFILE_ID,
    sourcePath,
    preserveSource: true,
    blueprintId: input.blueprintId,
    targetMinecraftVersion: input.targetMinecraftVersion,
    resourcePackExportMode,
    dataPackExportMode,
    resourcePackPath,
    dataPackPath,
    enablePluginMode: input.enablePluginMode === true,
    modelExportRoot,
    textureExportRoot,
    blueprintFormatId: ANIMATED_JAVA_AUTHORITY.blueprintFormatId,
    blueprintCodecId: ANIMATED_JAVA_AUTHORITY.blueprintCodecId,
    requiresAnimatedJavaPlugin: true,
    implicitProviderConversion: false,
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
}

module.exports = {
  ANIMATED_JAVA_AUTHORITY,
  AnimatedJavaContractError,
  validateAnimatedJavaBlueprint,
  createAnimatedJavaExportPlan,
};
