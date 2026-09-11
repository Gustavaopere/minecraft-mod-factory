'use strict';

const azurelib = require('../core/provider-adapter/azurelib_adapter.js');

function fail(code, message) {
  throw new azurelib.AzureLibContractError(code, message);
}

function normalizedSourcePath(value) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('AZURELIB_SOURCE_NOT_SAVED', 'Active AzureLib project must be saved as a .bbmodel before provider export.');
  }
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith('.bbmodel')) {
    fail('AZURELIB_SOURCE_MUST_BE_BBMODEL', 'Active AzureLib project source must remain a .bbmodel file.');
  }
  return normalized;
}

function cloneJsonDocument(value, code, label) {
  if (typeof value === 'string') {
    try {
      return JSON.parse(value);
    } catch (error) {
      fail(code, `${label} compiler returned invalid JSON: ${error.message}`);
    }
  }
  if (!value || typeof value !== 'object') fail(code, `${label} compiler must return JSON text or an object.`);
  try {
    return JSON.parse(JSON.stringify(value));
  } catch (error) {
    fail(code, `${label} compiler returned a non-serializable object: ${error.message}`);
  }
}

function deepFreezeJsonDocument(value) {
  if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreezeJsonDocument(child);
  return Object.freeze(value);
}

function createBlockbenchAzureLibAdapter(bb) {
  if (!bb || typeof bb !== 'object') fail('AZURELIB_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  const project = bb.Blockbench?.Project;
  if (!project || project.format?.id !== azurelib.AZURELIB_AUTHORITY.blockbenchFormatId) {
    fail('AZURELIB_PROJECT_FORMAT_REQUIRED', 'Active Blockbench project must use the AzureLib Animator format azure_model.');
  }
  const savedSourcePath = normalizedSourcePath(project.save_path);
  if (typeof bb.Codecs?.bedrock?.compile !== 'function') {
    fail('AZURELIB_MODEL_CODEC_UNAVAILABLE', 'Blockbench Codecs.bedrock.compile is required by the audited AzureLib Animator 2.1.5 integration.');
  }

  const trustedPreviews = new WeakSet();

  function sourcePath() {
    return savedSourcePath;
  }

  function animationCodec() {
    const codec = project.format?.animation_codec || bb.Format?.animation_codec || null;
    if (
      !codec
      || (codec.id !== undefined && codec.id !== azurelib.AZURELIB_AUTHORITY.animationCodecId)
      || typeof codec.compileFile !== 'function'
      || typeof codec.write !== 'function'
    ) {
      fail(
        'AZURELIB_ANIMATION_CODEC_UNAVAILABLE',
        'AzureLib Animator 2.1.5 AnimationCodec azure_animation with compileFile() and write() is required for animation export.',
      );
    }
    return codec;
  }

  function compileModelDocument() {
    const document = cloneJsonDocument(
      bb.Codecs.bedrock.compile(),
      'INVALID_AZURELIB_COMPILED_MODEL',
      'AzureLib model',
    );
    azurelib.validateAzureLibGeoDocument(document);
    return deepFreezeJsonDocument(document);
  }

  function compileAnimationArtifact() {
    const codec = animationCodec();
    const document = cloneJsonDocument(
      codec.compileFile(),
      'INVALID_AZURELIB_COMPILED_ANIMATION',
      'AzureLib animation',
    );
    azurelib.validateAzureLibAnimationDocument(document);

    let serializedContent;
    try {
      serializedContent = codec.write(document);
    } catch (error) {
      fail('INVALID_AZURELIB_SERIALIZED_ANIMATION', `AzureLib AnimationCodec write() failed: ${error.message}`);
    }
    if (typeof serializedContent !== 'string' || serializedContent.length === 0) {
      fail('INVALID_AZURELIB_SERIALIZED_ANIMATION', 'AzureLib AnimationCodec write() must return serialized JSON text.');
    }

    let serializedDocument;
    try {
      serializedDocument = JSON.parse(serializedContent);
    } catch (error) {
      fail('INVALID_AZURELIB_SERIALIZED_ANIMATION', `AzureLib AnimationCodec write() returned invalid JSON: ${error.message}`);
    }
    azurelib.validateAzureLibAnimationDocument(serializedDocument);

    return Object.freeze({
      document: deepFreezeJsonDocument(document),
      serializedContent,
    });
  }

  function compileAnimationDocument() {
    return compileAnimationArtifact().document;
  }

  function previewExport(request) {
    if (!request || typeof request !== 'object' || Array.isArray(request)) {
      fail('INVALID_AZURELIB_EXPORT_PLAN', 'Export request must be an object.');
    }
    const plan = azurelib.createAzureLibExportPlan({...request, sourcePath: savedSourcePath});
    const modelDocument = compileModelDocument();
    const animationArtifact = request.includeAnimations === true ? compileAnimationArtifact() : null;
    const artifacts = plan.artifacts.map((artifact) => {
      if (artifact.kind === 'model') {
        return Object.freeze({kind: artifact.kind, path: artifact.path, document: modelDocument});
      }
      return Object.freeze({
        kind: artifact.kind,
        path: artifact.path,
        document: animationArtifact.document,
        serializedContent: animationArtifact.serializedContent,
      });
    });
    const preview = Object.freeze({
      plan,
      artifacts: Object.freeze(artifacts),
      runtimeEvidence: 'UNPROVEN',
    });
    trustedPreviews.add(preview);
    return preview;
  }

  function stageExport(preview, writer) {
    if (!preview || typeof preview !== 'object' || !trustedPreviews.has(preview)) {
      fail('INVALID_AZURELIB_EXPORT_PREVIEW', 'Only a validated preview produced by this adapter can be staged.');
    }
    if (!writer || typeof writer.writeText !== 'function') {
      fail('INVALID_AZURELIB_EXPORT_WRITER', 'Export writer must provide writeText(path, content).');
    }
    for (const artifact of preview.artifacts) {
      if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
        fail('AZURELIB_SOURCE_OVERWRITE_FORBIDDEN', 'Provider staging must never overwrite the source .bbmodel.');
      }
      const content = artifact.kind === 'animation'
        ? artifact.serializedContent
        : JSON.stringify(artifact.document, null, 2);
      writer.writeText(artifact.path, content.endsWith('\n') ? content : `${content}\n`);
    }
    return Object.freeze({
      ok: true,
      staged: preview.artifacts.length,
      sourcePath: preview.plan.sourcePath,
      preserveSource: true,
      runtimeEvidence: 'UNPROVEN',
    });
  }

  return Object.freeze({
    sourcePath,
    compileModelDocument,
    compileAnimationDocument,
    previewExport,
    stageExport,
  });
}

module.exports = {
  createBlockbenchAzureLibAdapter,
};
