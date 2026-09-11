'use strict';

const azurelib = require('../core/provider-adapter/azurelib_adapter.js');
const common = require('./provider_adapter_common.js');

function fail(code, message) {
  throw new azurelib.AzureLibContractError(code, message);
}

function compileAnimationArtifact({bb, project, fail: failProvider, cloneJsonDocument, deepFreezeJsonDocument}) {
  const codec = project.format?.animation_codec || bb.Format?.animation_codec || null;
  if (
    !codec
    || (codec.id !== undefined && codec.id !== azurelib.AZURELIB_AUTHORITY.animationCodecId)
    || typeof codec.compileFile !== 'function'
    || typeof codec.write !== 'function'
  ) {
    failProvider(
      'AZURELIB_ANIMATION_CODEC_UNAVAILABLE',
      'AzureLib Animator 2.1.5 AnimationCodec azure_animation with compileFile() and write() is required for animation export.',
    );
  }

  const document = cloneJsonDocument(codec.compileFile(), {
    fail: failProvider,
    code: 'INVALID_AZURELIB_COMPILED_ANIMATION',
    label: 'AzureLib animation',
  });
  azurelib.validateAzureLibAnimationDocument(document);

  let serializedContent;
  try {
    serializedContent = codec.write(document);
  } catch (error) {
    failProvider(
      'INVALID_AZURELIB_SERIALIZED_ANIMATION',
      `AzureLib AnimationCodec write() failed: ${error.message}`,
    );
  }
  if (typeof serializedContent !== 'string' || serializedContent.length === 0) {
    failProvider(
      'INVALID_AZURELIB_SERIALIZED_ANIMATION',
      'AzureLib AnimationCodec write() must return serialized JSON text.',
    );
  }

  let serializedDocument;
  try {
    serializedDocument = JSON.parse(serializedContent);
  } catch (error) {
    failProvider(
      'INVALID_AZURELIB_SERIALIZED_ANIMATION',
      `AzureLib AnimationCodec write() returned invalid JSON: ${error.message}`,
    );
  }
  azurelib.validateAzureLibAnimationDocument(serializedDocument);

  return {
    document: deepFreezeJsonDocument(document),
    serializedContent,
  };
}

function createBlockbenchAzureLibAdapter(bb) {
  return common.createProviderBlockbenchAdapter(bb, {
    fail,
    blockbenchUnavailableCode: 'AZURELIB_BLOCKBENCH_UNAVAILABLE',
    blockbenchUnavailableMessage: 'Blockbench API object is required.',
    projectFormatId: azurelib.AZURELIB_AUTHORITY.blockbenchFormatId,
    projectFormatCode: 'AZURELIB_PROJECT_FORMAT_REQUIRED',
    projectFormatMessage: 'Active Blockbench project must use the AzureLib Animator format azure_model.',
    sourcePathOptions: {
      notSavedCode: 'AZURELIB_SOURCE_NOT_SAVED',
      sourceMustBeBbmodelCode: 'AZURELIB_SOURCE_MUST_BE_BBMODEL',
      notSavedMessage: 'Active AzureLib project must be saved as a .bbmodel before provider export.',
      sourceMustBeBbmodelMessage: 'Active AzureLib project source must remain a .bbmodel file.',
    },
    modelCodecUnavailableCode: 'AZURELIB_MODEL_CODEC_UNAVAILABLE',
    modelCodecUnavailableMessage: 'Blockbench Codecs.bedrock.compile is required by the audited AzureLib Animator 2.1.5 integration.',
    invalidCompiledModelCode: 'INVALID_AZURELIB_COMPILED_MODEL',
    modelLabel: 'AzureLib model',
    validateModelDocument: azurelib.validateAzureLibGeoDocument,
    compileAnimationArtifact,
    createExportPlan: azurelib.createAzureLibExportPlan,
    invalidExportPlanCode: 'INVALID_AZURELIB_EXPORT_PLAN',
    invalidExportPreviewCode: 'INVALID_AZURELIB_EXPORT_PREVIEW',
    invalidExportPreviewMessage: 'Only a validated preview produced by this adapter can be staged.',
    invalidExportWriterCode: 'INVALID_AZURELIB_EXPORT_WRITER',
    sourceOverwriteCode: 'AZURELIB_SOURCE_OVERWRITE_FORBIDDEN',
    sourceOverwriteMessage: 'Provider staging must never overwrite the source .bbmodel.',
  });
}

module.exports = {
  createBlockbenchAzureLibAdapter,
};
