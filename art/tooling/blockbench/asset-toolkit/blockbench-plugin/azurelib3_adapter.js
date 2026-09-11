'use strict';

const azurelib3 = require('../core/provider-adapter/azurelib3_adapter.js');

function fail(code, message) {
  throw new azurelib3.AzureLib3ContractError(code, message);
}

function normalizedSourcePath(value) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('AZURELIB3_SOURCE_NOT_SAVED', 'Active AzureLib project must be saved as a .bbmodel before provider export.');
  }
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith('.bbmodel')) {
    fail('AZURELIB3_SOURCE_MUST_BE_BBMODEL', 'Active AzureLib project source must remain a .bbmodel file.');
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
  if (!value || typeof value !== 'object') {
    fail(code, `${label} compiler must return JSON text or an object.`);
  }
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

function createBlockbenchAzureLib3Adapter(bb) {
  if (!bb || typeof bb !== 'object') {
    fail('AZURELIB3_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  }
  if (bb.Blockbench?.isWeb !== false) {
    fail('AZURELIB3_DESKTOP_REQUIRED', 'AzureLib provider export requires desktop Blockbench.');
  }

  const project = bb.Blockbench?.Project;
  if (!project || project.format?.id !== azurelib3.AZURELIB3_AUTHORITY.blockbenchFormatId) {
    fail('AZURELIB3_PROJECT_FORMAT_REQUIRED', 'Active Blockbench project must use the AzureLib plugin format azure_model.');
  }
  const savedSourcePath = normalizedSourcePath(project.save_path);
  if (typeof bb.Codecs?.bedrock?.compile !== 'function') {
    fail('AZURELIB3_MODEL_CODEC_UNAVAILABLE', 'Blockbench Codecs.bedrock.compile is required by the audited AzureLib 2.1.5 integration.');
  }

  const trustedPreviews = new WeakSet();

  function sourcePath() {
    return savedSourcePath;
  }

  function animationCodec() {
    const codec = project.format?.animation_codec;
    if (!codec || typeof codec.compileFile !== 'function' || typeof codec.write !== 'function') {
      fail('AZURELIB3_ANIMATION_CODEC_UNAVAILABLE', 'The active azure_model format must expose animation_codec.compileFile and animation_codec.write from azurelib_utils 2.1.5.');
    }
    return codec;
  }

  function compileModelDocument() {
    const document = cloneJsonDocument(
      bb.Codecs.bedrock.compile(),
      'INVALID_AZURELIB3_COMPILED_MODEL',
      'AzureLib model',
    );
    azurelib3.validateAzureLib3GeoDocument(document);
    return deepFreezeJsonDocument(document);
  }

  function compileAnimationDocument() {
    const document = cloneJsonDocument(
      animationCodec().compileFile(),
      'INVALID_AZURELIB3_COMPILED_ANIMATION',
      'AzureLib animation',
    );
    azurelib3.validateAzureLib3AnimationDocument(document);
    return deepFreezeJsonDocument(document);
  }

  function previewExport(request) {
    if (!request || typeof request !== 'object' || Array.isArray(request)) {
      fail('INVALID_AZURELIB3_EXPORT_PLAN', 'Export request must be an object.');
    }
    const plan = azurelib3.createAzureLib3ExportPlan({...request, sourcePath: savedSourcePath});
    const modelDocument = compileModelDocument();
    const animationDocument = request.includeAnimations === true ? compileAnimationDocument() : null;
    const artifacts = plan.artifacts.map((artifact) => Object.freeze({
      kind: artifact.kind,
      path: artifact.path,
      document: artifact.kind === 'model' ? modelDocument : animationDocument,
    }));
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
      fail('INVALID_AZURELIB3_EXPORT_PREVIEW', 'Only a validated preview produced by this adapter can be staged.');
    }
    if (!writer || typeof writer.writeText !== 'function') {
      fail('INVALID_AZURELIB3_EXPORT_WRITER', 'Export writer must provide writeText(path, content).');
    }

    for (const artifact of preview.artifacts) {
      if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
        fail('AZURELIB3_SOURCE_OVERWRITE_FORBIDDEN', 'Provider staging must never overwrite the source .bbmodel.');
      }

      if (artifact.kind === 'animation') {
        const serialized = animationCodec().write(artifact.document, artifact.path);
        if (typeof serialized !== 'string') {
          fail('INVALID_AZURELIB3_ANIMATION_SERIALIZATION', 'AzureLib animation_codec.write must return serialized JSON text.');
        }
        writer.writeText(artifact.path, serialized);
      } else {
        writer.writeText(artifact.path, `${JSON.stringify(artifact.document, null, 2)}\n`);
      }
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
  createBlockbenchAzureLib3Adapter,
};
