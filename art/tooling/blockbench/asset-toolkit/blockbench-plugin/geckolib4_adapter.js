'use strict';

const geckolib4 = require('../core/provider-adapter/geckolib4_adapter.js');

function fail(code, message) {
  throw new geckolib4.GeckoLib4ContractError(code, message);
}

function normalizedSourcePath(value) {
  if (typeof value !== 'string' || value.length === 0) fail('GECKOLIB4_SOURCE_NOT_SAVED', 'Active GeckoLib project must be saved as a .bbmodel before provider export.');
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith('.bbmodel')) fail('GECKOLIB4_SOURCE_MUST_BE_BBMODEL', 'Active GeckoLib project source must remain a .bbmodel file.');
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

function createBlockbenchGeckoLib4Adapter(bb) {
  if (!bb || typeof bb !== 'object') fail('GECKOLIB4_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  const project = bb.Blockbench?.Project;
  if (!project || project.format?.id !== 'geckolib_model') {
    fail('GECKOLIB4_PROJECT_FORMAT_REQUIRED', 'Active Blockbench project must use the GeckoLib plugin format geckolib_model.');
  }
  const savedSourcePath = normalizedSourcePath(project.save_path);
  if (typeof bb.Codecs?.bedrock?.compile !== 'function') {
    fail('GECKOLIB4_MODEL_CODEC_UNAVAILABLE', 'Blockbench Codecs.bedrock.compile is required by the audited GeckoLib 4.2.5 integration.');
  }

  const trustedPreviews = new WeakSet();

  function sourcePath() {
    return savedSourcePath;
  }

  function compileModelDocument() {
    const document = cloneJsonDocument(bb.Codecs.bedrock.compile(), 'INVALID_GECKOLIB4_COMPILED_MODEL', 'GeckoLib model');
    geckolib4.validateGeckoLib4GeoDocument(document);
    return document;
  }

  function compileAnimationDocument() {
    if (typeof bb.Animator?.buildFile !== 'function') {
      fail('GECKOLIB4_ANIMATION_CODEC_UNAVAILABLE', 'Blockbench Animator.buildFile is required by the audited GeckoLib 4.2.5 integration.');
    }
    const document = cloneJsonDocument(bb.Animator.buildFile(), 'INVALID_GECKOLIB4_COMPILED_ANIMATION', 'GeckoLib animation');
    geckolib4.validateGeckoLib4AnimationDocument(document);
    return document;
  }

  function previewExport(request) {
    if (!request || typeof request !== 'object' || Array.isArray(request)) fail('INVALID_GECKOLIB4_EXPORT_PLAN', 'Export request must be an object.');
    const plan = geckolib4.createGeckoLib4ExportPlan({...request, sourcePath: savedSourcePath});
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
      fail('INVALID_GECKOLIB4_EXPORT_PREVIEW', 'Only a validated preview produced by this adapter can be staged.');
    }
    if (!writer || typeof writer.writeText !== 'function') {
      fail('INVALID_GECKOLIB4_EXPORT_WRITER', 'Export writer must provide writeText(path, content).');
    }
    for (const artifact of preview.artifacts) {
      if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
        fail('GECKOLIB4_SOURCE_OVERWRITE_FORBIDDEN', 'Provider staging must never overwrite the source .bbmodel.');
      }
      writer.writeText(artifact.path, `${JSON.stringify(artifact.document, null, 2)}\n`);
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
  createBlockbenchGeckoLib4Adapter,
};
