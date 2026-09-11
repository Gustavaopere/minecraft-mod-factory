'use strict';

function normalizeSavedSourcePath(value, options) {
  const {
    fail,
    notSavedCode,
    sourceMustBeBbmodelCode,
    notSavedMessage,
    sourceMustBeBbmodelMessage,
  } = options;
  if (typeof value !== 'string' || value.length === 0) fail(notSavedCode, notSavedMessage);
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith('.bbmodel')) {
    fail(sourceMustBeBbmodelCode, sourceMustBeBbmodelMessage);
  }
  return normalized;
}

function cloneJsonDocument(value, options) {
  const {fail, code, label} = options;
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

function createProviderBlockbenchAdapter(bb, config) {
  const {
    fail,
    blockbenchUnavailableCode,
    blockbenchUnavailableMessage,
    projectFormatId,
    projectFormatCode,
    projectFormatMessage,
    sourcePathOptions,
    modelCodecUnavailableCode,
    modelCodecUnavailableMessage,
    invalidCompiledModelCode,
    modelLabel,
    validateModelDocument,
    compileAnimationArtifact,
    createExportPlan,
    invalidExportPlanCode,
    invalidExportPreviewCode,
    invalidExportPreviewMessage,
    invalidExportWriterCode,
    sourceOverwriteCode,
    sourceOverwriteMessage,
  } = config;

  if (!bb || typeof bb !== 'object') {
    fail(blockbenchUnavailableCode, blockbenchUnavailableMessage);
  }
  const project = bb.Blockbench?.Project;
  if (!project || project.format?.id !== projectFormatId) {
    fail(projectFormatCode, projectFormatMessage);
  }
  const savedSourcePath = normalizeSavedSourcePath(project.save_path, {fail, ...sourcePathOptions});
  if (typeof bb.Codecs?.bedrock?.compile !== 'function') {
    fail(modelCodecUnavailableCode, modelCodecUnavailableMessage);
  }

  const trustedPreviews = new WeakSet();

  function sourcePath() {
    return savedSourcePath;
  }

  function compileModelDocument() {
    const document = cloneJsonDocument(bb.Codecs.bedrock.compile(), {
      fail,
      code: invalidCompiledModelCode,
      label: modelLabel,
    });
    validateModelDocument(document);
    return deepFreezeJsonDocument(document);
  }

  function compileAnimationArtifactInternal() {
    const artifact = compileAnimationArtifact({
      bb,
      project,
      fail,
      cloneJsonDocument,
      deepFreezeJsonDocument,
    });
    if (!artifact || typeof artifact !== 'object' || !artifact.document) {
      throw new TypeError('compileAnimationArtifact must return an object containing document.');
    }
    return Object.freeze(artifact);
  }

  function compileAnimationDocument() {
    return compileAnimationArtifactInternal().document;
  }

  function previewExport(request) {
    if (!request || typeof request !== 'object' || Array.isArray(request)) {
      fail(invalidExportPlanCode, 'Export request must be an object.');
    }
    const plan = createExportPlan({...request, sourcePath: savedSourcePath});
    const modelDocument = compileModelDocument();
    const animationArtifact = request.includeAnimations === true
      ? compileAnimationArtifactInternal()
      : null;
    const artifacts = plan.artifacts.map((artifact) => {
      if (artifact.kind === 'model') {
        return Object.freeze({kind: artifact.kind, path: artifact.path, document: modelDocument});
      }
      const output = {
        kind: artifact.kind,
        path: artifact.path,
        document: animationArtifact.document,
      };
      if (typeof animationArtifact.serializedContent === 'string') {
        output.serializedContent = animationArtifact.serializedContent;
      }
      return Object.freeze(output);
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
      fail(invalidExportPreviewCode, invalidExportPreviewMessage);
    }
    if (!writer || typeof writer.writeText !== 'function') {
      fail(invalidExportWriterCode, 'Export writer must provide writeText(path, content).');
    }
    for (const artifact of preview.artifacts) {
      if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
        fail(sourceOverwriteCode, sourceOverwriteMessage);
      }
      const content = typeof artifact.serializedContent === 'string'
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
  cloneJsonDocument,
  deepFreezeJsonDocument,
  createProviderBlockbenchAdapter,
};
