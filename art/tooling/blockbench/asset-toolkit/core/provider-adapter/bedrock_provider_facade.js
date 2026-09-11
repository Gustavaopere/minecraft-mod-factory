'use strict';

const bedrock = require('./bedrock_provider_common.js');

function defaultCodes(prefix) {
  return Object.freeze({
    invalidGeoDocument: `INVALID_${prefix}_GEO_DOCUMENT`,
    unsupportedGeoFormat: `UNSUPPORTED_${prefix}_GEO_FORMAT`,
    invalidLocator: `INVALID_${prefix}_LOCATOR`,
    invalidString: `INVALID_${prefix}_STRING`,
    invalidAnimationDocument: `INVALID_${prefix}_ANIMATION_DOCUMENT`,
    invalidNumber: `INVALID_${prefix}_NUMBER`,
    invalidLoop: `INVALID_${prefix}_LOOP`,
    invalidKeyframe: `INVALID_${prefix}_KEYFRAME`,
    invalidTimestamp: `INVALID_${prefix}_TIMESTAMP`,
    invalidEffects: `INVALID_${prefix}_EFFECTS`,
    unsupportedAnimationFormat: `UNSUPPORTED_${prefix}_ANIMATION_FORMAT`,
    invalidMarker: `INVALID_${prefix}_EFFECT_MARKER`,
    unsupportedMarker: `UNSUPPORTED_${prefix}_EFFECT_MARKER`,
    invalidExportPlan: `INVALID_${prefix}_EXPORT_PLAN`,
    invalidProfile: `INVALID_${prefix}_PROFILE`,
    invalidSourcePath: `INVALID_${prefix}_SOURCE_PATH`,
    sourceMustBeBbmodel: `${prefix}_SOURCE_MUST_BE_BBMODEL`,
    invalidPath: `INVALID_${prefix}_PATH`,
    invalidResourceName: `INVALID_${prefix}_RESOURCE_NAME`,
  });
}

function createBedrockProviderFacade(config) {
  const baseCodes = defaultCodes(config.codePrefix);
  const codes = Object.freeze({...baseCodes, ...(config.codeOverrides || {})});
  const shared = {
    fail: config.fail,
    trimStrings: config.trimStrings === true,
  };

  const geoOptions = Object.freeze({
    ...shared,
    invalidDocumentCode: codes.invalidGeoDocument,
    unsupportedFormatCode: codes.unsupportedGeoFormat,
    invalidLocatorCode: codes.invalidLocator,
    invalidStringCode: codes.invalidString,
    locatorNameCode: codes.locatorName || codes.invalidString,
    providerLabel: config.geoProviderLabel || config.providerLabel,
    formatVersions: config.formatVersions,
    rejectRootMetadata: config.rejectRootMetadata,
  });

  const animationOptions = Object.freeze({
    ...shared,
    invalidDocumentCode: codes.invalidAnimationDocument,
    invalidStringCode: codes.invalidString,
    invalidNumberCode: codes.invalidNumber,
    invalidLoopCode: codes.invalidLoop,
    invalidKeyframeCode: codes.invalidKeyframe,
    invalidTimestampCode: codes.invalidTimestamp,
    invalidEffectsCode: codes.invalidEffects,
    effectStringCode: codes.effectValidationString || codes.invalidEffects,
    loopValues: config.loopValues,
    validateKeyframeLeaf: config.validateKeyframeLeaf,
    leafIndicatorFields: config.leafIndicatorFields,
    expectedFormatVersion: config.expectedFormatVersion,
    unsupportedFormatCode: codes.unsupportedAnimationFormat,
    rejectRootMetadata: config.rejectRootMetadata,
    validateIncludes: config.validateIncludes,
    requireParticleEffect: config.requireParticleEffect,
    requireNonEmptyTimeline: config.requireNonEmptyTimeline,
  });

  const markerOptions = Object.freeze({
    ...shared,
    invalidMarkerCode: codes.invalidMarker,
    unsupportedMarkerCode: codes.unsupportedMarker,
    invalidNumberCode: codes.invalidNumber,
    stringCode: codes.markerString || codes.invalidMarker,
    providerLabel: config.providerLabel,
    requireParticleEffect: config.requireParticleEffect,
    requireNonEmptyTimeline: config.requireNonEmptyTimeline,
  });

  const exportOptions = Object.freeze({
    ...shared,
    profileIds: config.profileIds,
    providerFamily: config.providerFamily,
    providerLabel: config.providerLabel,
    invalidPlanCode: codes.invalidExportPlan,
    invalidProfileCode: codes.invalidProfile,
    invalidSourcePathCode: codes.invalidSourcePath,
    sourceMustBeBbmodelCode: codes.sourceMustBeBbmodel,
    invalidPathCode: codes.invalidPath,
    invalidResourceNameCode: codes.invalidResourceName,
    invalidStringCode: codes.invalidString,
  });

  function createExportPlan(input) {
    if (config.prevalidateExport) config.prevalidateExport(input);
    return bedrock.createExportPlan(input, exportOptions);
  }

  return Object.freeze({
    validateGeoDocument(value) {
      return bedrock.validateGeoDocument(value, geoOptions);
    },
    validateAnimationDocument(value) {
      return bedrock.validateAnimationDocument(value, animationOptions);
    },
    serializeEffectMarker(marker, providerData) {
      return bedrock.serializeEffectMarker(marker, providerData, markerOptions);
    },
    createExportPlan,
  });
}

module.exports = {
  createBedrockProviderFacade,
};
