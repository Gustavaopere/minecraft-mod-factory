'use strict';

const {isPlainObject, rejectUnknownFields} = require('../common/contract_utils.js');
const bedrock = require('./bedrock_provider_common.js');
const {createBedrockProviderFacade} = require('./bedrock_provider_facade.js');

const AZURELIB_AUTHORITY = Object.freeze({
  providerFamily: 'azurelib',
  runtimeVersion: '3.1.11',
  runtimeSource: 'AzureDoom/AzureLib',
  runtimeRef: '4aac02dcefff5440874b3ec64871a1cd0feffadf',
  blockbenchPluginId: 'azurelib_utils',
  blockbenchPluginVersion: '2.1.5',
  blockbenchPluginSource: 'JannisX11/blockbench-plugins',
  blockbenchPluginRef: '38862eb66b219995b09926488f7d1084a0fb6b3a',
  blockbenchFormatId: 'azure_model',
  animationCodecId: 'azure_animation',
  animationFormatVersion: '1.8.0',
});

const AZURELIB_PROFILE_IDS = new Set([
  'azurelib_entity',
  'azurelib_item',
  'azurelib_block',
  'azurelib_armor',
]);
const GEO_FORMAT_VERSIONS = new Set(['1.12.0', '1.14.0', '1.21.0']);
const LOOP_VALUES = new Set(['false', 'true', 'play_once', 'loop', 'hold_on_last_frame']);
const BEDROCK_LERP_MODES = new Set(['linear', 'catmullrom']);
const AZURE_KEYFRAME_FIELDS = new Set(['vector', 'easing', 'easingArgs']);
const BEDROCK_KEYFRAME_FIELDS = new Set(['pre', 'post', 'lerp_mode']);
const RESOURCE_LOCATION = /^[a-z0-9_.-]+:[a-z0-9/._-]+$/;

class AzureLibContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'AzureLibContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new AzureLibContractError(code, message);
}

function nonEmptyString(value, field, code = 'INVALID_AZURELIB_STRING') {
  if (typeof value !== 'string' || !value.trim()) fail(code, `${field} must be a non-empty string.`);
  return value;
}

function rejectAuthoringMetadata(value, artifact) {
  if (Object.prototype.hasOwnProperty.call(value, 'azureIKChains')) {
    fail(
      'AZURELIB_AUTHORING_METADATA_IN_RUNTIME_ARTIFACT',
      `azureIKChains is Blockbench authoring metadata and must not be serialized into AzureLib ${artifact} runtime artifacts.`,
    );
  }
}

function validateVectorExpression(value, field) {
  bedrock.validateVectorExpression(value, field, fail, 'INVALID_AZURELIB_KEYFRAME', true);
}

function validateBedrockVector(value, field) {
  if (Array.isArray(value)) {
    validateVectorExpression(value, field);
    return;
  }
  if (isPlainObject(value) && Array.isArray(value.vector)) {
    rejectUnknownFields(value, new Set(['vector']), fail, 'INVALID_AZURELIB_KEYFRAME', field);
    validateVectorExpression(value.vector, `${field}.vector`);
    return;
  }
  fail('INVALID_AZURELIB_KEYFRAME', `${field} must be a vector or an object containing vector.`);
}

function validateKeyframeLeaf(value, field) {
  if (Number.isFinite(value) || (typeof value === 'string' && value.trim())) return;
  if (Array.isArray(value)) {
    validateVectorExpression(value, field);
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_AZURELIB_KEYFRAME', `${field} has an unsupported keyframe shape.`);

  const hasAzureShape = value.vector !== undefined || value.easing !== undefined || value.easingArgs !== undefined;
  const hasBedrockShape = value.pre !== undefined || value.post !== undefined || value.lerp_mode !== undefined;
  if (hasAzureShape && hasBedrockShape) {
    fail(
      'INVALID_AZURELIB_KEYFRAME',
      `${field} must not mix AzureLib vector/easing fields with Bedrock pre/post/lerp_mode fields in one keyframe.`,
    );
  }

  if (hasAzureShape) {
    rejectUnknownFields(value, AZURE_KEYFRAME_FIELDS, fail, 'INVALID_AZURELIB_KEYFRAME', field);
    if (value.vector === undefined) {
      fail('INVALID_AZURELIB_KEYFRAME', `${field}.vector is required for AzureLib easing keyframes.`);
    }
    validateVectorExpression(value.vector, `${field}.vector`);
    if (value.easing !== undefined) {
      nonEmptyString(value.easing, `${field}.easing`, 'INVALID_AZURELIB_KEYFRAME');
    }
    if (value.easingArgs !== undefined && (!Array.isArray(value.easingArgs) || !value.easingArgs.every(Number.isFinite))) {
      fail('INVALID_AZURELIB_KEYFRAME', `${field}.easingArgs must contain finite numbers.`);
    }
    return;
  }

  if (hasBedrockShape) {
    rejectUnknownFields(value, BEDROCK_KEYFRAME_FIELDS, fail, 'INVALID_AZURELIB_KEYFRAME', field);
    if (value.pre !== undefined) validateBedrockVector(value.pre, `${field}.pre`);
    if (value.post !== undefined) validateBedrockVector(value.post, `${field}.post`);
    if (value.pre === undefined && value.post === undefined) {
      fail('INVALID_AZURELIB_KEYFRAME', `${field} must define pre or post when using Bedrock keyframe fields.`);
    }
    if (value.lerp_mode !== undefined && !BEDROCK_LERP_MODES.has(value.lerp_mode)) {
      fail(
        'UNSUPPORTED_AZURELIB_LERP_MODE',
        `${field}.lerp_mode ${JSON.stringify(value.lerp_mode)} is not audited for AzureLib 3.1.11.`,
      );
    }
    return;
  }

  fail('INVALID_AZURELIB_KEYFRAME', `${field} has an unsupported keyframe object.`);
}

function validateIncludes(value) {
  if (value === undefined) return 0;
  if (!Array.isArray(value)) fail('INVALID_AZURELIB_INCLUDES', 'includes must be an array.');
  const claimedAnimations = new Set();
  value.forEach((entry, index) => {
    if (!isPlainObject(entry)) fail('INVALID_AZURELIB_INCLUDES', `includes[${index}] must be an object.`);
    rejectUnknownFields(
      entry,
      new Set(['file_id', 'animations']),
      fail,
      'INVALID_AZURELIB_INCLUDES',
      `includes[${index}]`,
    );
    const fileId = nonEmptyString(entry.file_id, `includes[${index}].file_id`, 'INVALID_AZURELIB_INCLUDES');
    if (!RESOURCE_LOCATION.test(fileId)) {
      fail('INVALID_AZURELIB_INCLUDES', `includes[${index}].file_id must be a Minecraft resource location.`);
    }
    if (!Array.isArray(entry.animations) || entry.animations.length === 0) {
      fail('INVALID_AZURELIB_INCLUDES', `includes[${index}].animations must be a non-empty string array.`);
    }
    for (const animationName of entry.animations) {
      const name = nonEmptyString(
        animationName,
        `includes[${index}] animation name`,
        'INVALID_AZURELIB_INCLUDES',
      );
      if (claimedAnimations.has(name)) {
        fail(
          'DUPLICATE_AZURELIB_INCLUDE_ANIMATION',
          `Animation ${JSON.stringify(name)} is claimed by more than one include entry.`,
        );
      }
      claimedAnimations.add(name);
    }
  });
  return value.length;
}

function prevalidateExport(input) {
  if (!isPlainObject(input)) fail('INVALID_AZURELIB_EXPORT_PLAN', 'Export plan request must be an object.');
  if (!AZURELIB_PROFILE_IDS.has(input.profileId)) {
    fail('INVALID_AZURELIB_PROFILE', `Profile ${JSON.stringify(input.profileId)} is not an AzureLib profile.`);
  }
  nonEmptyString(input.sourcePath, 'sourcePath', 'INVALID_AZURELIB_SOURCE_PATH');
  nonEmptyString(input.outputDirectory, 'outputDirectory', 'INVALID_AZURELIB_PATH');
  nonEmptyString(input.resourceName, 'resourceName', 'INVALID_AZURELIB_RESOURCE_NAME');
}

const provider = createBedrockProviderFacade({
  fail,
  codePrefix: 'AZURELIB',
  providerFamily: 'azurelib',
  providerLabel: 'AzureLib',
  geoProviderLabel: 'AzureLib 3.1.11',
  profileIds: AZURELIB_PROFILE_IDS,
  formatVersions: GEO_FORMAT_VERSIONS,
  loopValues: LOOP_VALUES,
  validateKeyframeLeaf,
  leafIndicatorFields: ['vector', 'easing', 'easingArgs', 'pre', 'post', 'lerp_mode'],
  expectedFormatVersion: AZURELIB_AUTHORITY.animationFormatVersion,
  rejectRootMetadata: rejectAuthoringMetadata,
  validateIncludes,
  requireParticleEffect: true,
  requireNonEmptyTimeline: true,
  trimStrings: true,
  prevalidateExport,
  codeOverrides: {
    invalidLoop: 'UNSUPPORTED_AZURELIB_LOOP',
    locatorName: 'INVALID_AZURELIB_LOCATOR',
    markerString: 'INVALID_AZURELIB_EFFECT_MARKER',
  },
});

module.exports = {
  AZURELIB_AUTHORITY,
  AzureLibContractError,
  validateAzureLibGeoDocument: provider.validateGeoDocument,
  validateAzureLibAnimationDocument: provider.validateAnimationDocument,
  serializeAzureLibEffectMarker: provider.serializeEffectMarker,
  createAzureLibExportPlan: provider.createExportPlan,
};
