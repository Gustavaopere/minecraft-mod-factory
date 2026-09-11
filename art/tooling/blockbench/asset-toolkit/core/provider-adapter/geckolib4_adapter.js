'use strict';

const {isPlainObject} = require('../common/contract_utils.js');
const bedrock = require('./bedrock_provider_common.js');

const GECKOLIB4_AUTHORITY = Object.freeze({
  providerFamily: 'geckolib4',
  runtimeVersion: '4.9.2',
  runtimeSource: 'bernie-g/geckolib',
  runtimeRef: 'd57fc640de083ae67ec0051a02b2b4fb22f4d02b',
  blockbenchPluginId: 'geckolib',
  blockbenchPluginVersion: '4.2.5',
  blockbenchPluginSource: 'JannisX11/blockbench-plugins',
  blockbenchPluginRef: '96d3b694de7d44077de68181711816153c442a6f',
});

const GECKOLIB4_PROFILE_IDS = new Set([
  'geckolib4_entity',
  'geckolib4_block_entity',
  'geckolib4_item',
  'geckolib4_armor',
]);
const GEO_FORMAT_VERSIONS = new Set(['1.12.0', '1.14.0', '1.21.0']);
const LOOP_VALUES = new Set(['false', 'play_once', 'true', 'loop', 'hold_on_last_frame']);

class GeckoLib4ContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'GeckoLib4ContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new GeckoLib4ContractError(code, message);
}

function validateVectorExpression(value, field) {
  bedrock.validateVectorExpression(value, field, fail, 'INVALID_GECKOLIB4_KEYFRAME');
}

function validateKeyframeLeaf(value, field) {
  if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0)) return;
  if (Array.isArray(value)) {
    validateVectorExpression(value, field);
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} has an unsupported keyframe shape.`);
  if (value.vector !== undefined) {
    validateVectorExpression(value.vector, `${field}.vector`);
    if (value.easing !== undefined && typeof value.easing !== 'string') {
      fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.easing must be a string.`);
    }
    if (value.easingArgs !== undefined && (!Array.isArray(value.easingArgs) || !value.easingArgs.every(Number.isFinite))) {
      fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.easingArgs must contain finite numbers.`);
    }
    return;
  }
  if (value.pre !== undefined) validateVectorExpression(value.pre, `${field}.pre`);
  if (value.post !== undefined) validateVectorExpression(value.post, `${field}.post`);
  if (value.pre === undefined && value.post === undefined) {
    fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must define vector, pre, or post.`);
  }
  if (value.lerp_mode !== undefined && typeof value.lerp_mode !== 'string') {
    fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.lerp_mode must be a string.`);
  }
}

function validateGeckoLib4GeoDocument(value) {
  return bedrock.validateGeoDocument(value, {
    fail,
    invalidDocumentCode: 'INVALID_GECKOLIB4_GEO_DOCUMENT',
    unsupportedFormatCode: 'UNSUPPORTED_GECKOLIB4_GEO_FORMAT',
    invalidLocatorCode: 'INVALID_GECKOLIB4_LOCATOR',
    invalidStringCode: 'INVALID_GECKOLIB4_STRING',
    providerLabel: 'GeckoLib 4.9.2',
    formatVersions: GEO_FORMAT_VERSIONS,
  });
}

function validateGeckoLib4AnimationDocument(value) {
  return bedrock.validateAnimationDocument(value, {
    fail,
    invalidDocumentCode: 'INVALID_GECKOLIB4_ANIMATION_DOCUMENT',
    invalidStringCode: 'INVALID_GECKOLIB4_STRING',
    invalidNumberCode: 'INVALID_GECKOLIB4_NUMBER',
    invalidLoopCode: 'INVALID_GECKOLIB4_LOOP',
    invalidKeyframeCode: 'INVALID_GECKOLIB4_KEYFRAME',
    invalidTimestampCode: 'INVALID_GECKOLIB4_TIMESTAMP',
    invalidEffectsCode: 'INVALID_GECKOLIB4_EFFECTS',
    effectStringCode: 'INVALID_GECKOLIB4_STRING',
    loopValues: LOOP_VALUES,
    validateKeyframeLeaf,
    leafIndicatorFields: ['vector', 'pre', 'post'],
  });
}

function serializeGeckoLib4EffectMarker(marker, providerData) {
  return bedrock.serializeEffectMarker(marker, providerData, {
    fail,
    invalidMarkerCode: 'INVALID_GECKOLIB4_EFFECT_MARKER',
    unsupportedMarkerCode: 'UNSUPPORTED_GECKOLIB4_EFFECT_MARKER',
    invalidNumberCode: 'INVALID_GECKOLIB4_NUMBER',
    stringCode: 'INVALID_GECKOLIB4_STRING',
    providerLabel: 'GeckoLib 4',
  });
}

function createGeckoLib4ExportPlan(input) {
  return bedrock.createExportPlan(input, {
    fail,
    profileIds: GECKOLIB4_PROFILE_IDS,
    providerFamily: 'geckolib4',
    providerLabel: 'GeckoLib 4',
    invalidPlanCode: 'INVALID_GECKOLIB4_EXPORT_PLAN',
    invalidProfileCode: 'INVALID_GECKOLIB4_PROFILE',
    invalidSourcePathCode: 'INVALID_GECKOLIB4_SOURCE_PATH',
    sourceMustBeBbmodelCode: 'GECKOLIB4_SOURCE_MUST_BE_BBMODEL',
    invalidPathCode: 'INVALID_GECKOLIB4_PATH',
    invalidResourceNameCode: 'INVALID_GECKOLIB4_RESOURCE_NAME',
    invalidStringCode: 'INVALID_GECKOLIB4_STRING',
  });
}

module.exports = {
  GECKOLIB4_AUTHORITY,
  GeckoLib4ContractError,
  validateGeckoLib4GeoDocument,
  validateGeckoLib4AnimationDocument,
  serializeGeckoLib4EffectMarker,
  createGeckoLib4ExportPlan,
};
