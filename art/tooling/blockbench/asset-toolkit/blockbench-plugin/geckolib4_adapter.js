'use strict';

const geckolib4 = require('../core/provider-adapter/geckolib4_adapter.js');
const common = require('./provider_adapter_common.js');

function fail(code, message) {
  throw new geckolib4.GeckoLib4ContractError(code, message);
}

function compileAnimationArtifact({bb, fail: failProvider, cloneJsonDocument, deepFreezeJsonDocument}) {
  if (typeof bb.Animator?.buildFile !== 'function') {
    failProvider(
      'GECKOLIB4_ANIMATION_CODEC_UNAVAILABLE',
      'Blockbench Animator.buildFile is required by the audited GeckoLib 4.2.5 integration.',
    );
  }
  const document = cloneJsonDocument(bb.Animator.buildFile(), {
    fail: failProvider,
    code: 'INVALID_GECKOLIB4_COMPILED_ANIMATION',
    label: 'GeckoLib animation',
  });
  geckolib4.validateGeckoLib4AnimationDocument(document);
  return {document: deepFreezeJsonDocument(document)};
}

function createBlockbenchGeckoLib4Adapter(bb) {
  return common.createProviderBlockbenchAdapter(bb, {
    fail,
    blockbenchUnavailableCode: 'GECKOLIB4_BLOCKBENCH_UNAVAILABLE',
    blockbenchUnavailableMessage: 'Blockbench API object is required.',
    projectFormatId: 'geckolib_model',
    projectFormatCode: 'GECKOLIB4_PROJECT_FORMAT_REQUIRED',
    projectFormatMessage: 'Active Blockbench project must use the GeckoLib plugin format geckolib_model.',
    sourcePathOptions: {
      notSavedCode: 'GECKOLIB4_SOURCE_NOT_SAVED',
      sourceMustBeBbmodelCode: 'GECKOLIB4_SOURCE_MUST_BE_BBMODEL',
      notSavedMessage: 'Active GeckoLib project must be saved as a .bbmodel before provider export.',
      sourceMustBeBbmodelMessage: 'Active GeckoLib project source must remain a .bbmodel file.',
    },
    modelCodecUnavailableCode: 'GECKOLIB4_MODEL_CODEC_UNAVAILABLE',
    modelCodecUnavailableMessage: 'Blockbench Codecs.bedrock.compile is required by the audited GeckoLib 4.2.5 integration.',
    invalidCompiledModelCode: 'INVALID_GECKOLIB4_COMPILED_MODEL',
    modelLabel: 'GeckoLib model',
    validateModelDocument: geckolib4.validateGeckoLib4GeoDocument,
    compileAnimationArtifact,
    createExportPlan: geckolib4.createGeckoLib4ExportPlan,
    invalidExportPlanCode: 'INVALID_GECKOLIB4_EXPORT_PLAN',
    invalidExportPreviewCode: 'INVALID_GECKOLIB4_EXPORT_PREVIEW',
    invalidExportPreviewMessage: 'Only a validated preview produced by this adapter can be staged.',
    invalidExportWriterCode: 'INVALID_GECKOLIB4_EXPORT_WRITER',
    sourceOverwriteCode: 'GECKOLIB4_SOURCE_OVERWRITE_FORBIDDEN',
    sourceOverwriteMessage: 'Provider staging must never overwrite the source .bbmodel.',
  });
}

module.exports = {
  createBlockbenchGeckoLib4Adapter,
};
