'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const {createProjectSnapshot} = require('./live-bridge/project_snapshot.js');
const {buildSessionFingerprint} = require('./live-bridge/fingerprint.js');
const standalone = require('./asset_toolkit.js');

function sampleProject() {
  const root = {name: 'root', uuid: 'bone-root', origin: [0, 0, 0], parent: null};
  return {
    name: 'qa_manifest_sample',
    save_path: '/workspace/source/qa_manifest_sample.bbmodel',
    format: {id: 'free'},
    groups: [root],
    elements: [{
      name: 'body',
      uuid: 'cube-body',
      from: [0, 0, 0],
      to: [4, 4, 4],
      origin: [2, 2, 2],
      parent: root,
      faces: {
        north: {enabled: true, texture: '#tex-main', uv: [0, 0, 4, 4]},
      },
    }],
    textures: [{name: 'main.png', uuid: 'tex-main', width: 16, height: 16, internal: true, source: 'data:image/png;base64,AAAA'}],
    animations: [],
    metadata: {assetId: 'factory:qa_manifest_sample', kind: 'entity'},
  };
}

function sessionFingerprint(projectRevision) {
  return buildSessionFingerprint({
    minecraftVersion: '1.21.1',
    loader: 'neoforge',
    javaVersion: '21',
    blockbenchVersion: '5.1.6',
    toolkitVersion: 'pr14-test',
    protocolVersion: '1',
    installedExtensions: [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
    physicalProviders: [{modId: 'geckolib', modVersion: '4.9.2'}],
    activeProviderProfile: 'geckolib4_entity',
    projectFormat: 'free',
    projectRevision,
  });
}

function validInput(overrides = {}) {
  const project = sampleProject();
  const projectSnapshot = createProjectSnapshot(project);
  return {
    project,
    projectSnapshot,
    providerProfileId: 'geckolib4_entity',
    sessionFingerprint: sessionFingerprint(projectSnapshot.projectRevision),
    sourceArtifacts: [{
      kind: 'blockbench_source',
      path: '/workspace/source/qa_manifest_sample.bbmodel',
      content: '{"source":"bbmodel"}',
      preserve: true,
    }],
    captureEvidence: [{
      id: 'front',
      cameraPreset: 'front',
      resolution: [512, 512],
      content: 'capture-front-v1',
    }],
    visualQa: {
      status: 'PASS',
      evidenceId: 'visual-review-001',
      checks: ['silhouette', 'proportions', 'clipping', 'readability'],
    },
    exportPlan: {
      roots: [{
        id: 'target_mod_resources',
        path: '/workspace/mod/src/main/resources',
        allowKinds: ['model', 'animation', 'texture'],
      }],
      staging: {
        rootId: 'target_mod_resources',
        relativePath: '.factory-staging/qa_manifest_sample',
        state: 'VALIDATED',
      },
      outputs: [{
        kind: 'model',
        rootId: 'target_mod_resources',
        relativePath: 'assets/factory/geo/qa_manifest_sample.geo.json',
        content: '{"format_version":"1.12.0"}',
      }],
    },
    runtimeTarget: {
      minecraftVersion: '1.21.1',
      loader: 'neoforge',
      loaderVersion: '21.1.248',
      javaVersion: '21',
    },
    runtimeQa: {
      status: 'PASS',
      evidenceId: 'runtime-smoke-001',
    },
    handoffDestinations: [{
      kind: 'mod_resources',
      rootId: 'target_mod_resources',
      namespace: 'factory',
    }],
    previousExportArtifacts: [],
    ...overrides,
  };
}

test('PR14 exposes a unified QA/export manifest API without adding an export side effect', () => {
  assert.equal(typeof core.createUnifiedQaExportManifest, 'function');
  assert.equal(core.exportAsset, undefined);
  assert.equal(core.promoteExport, undefined);
});

test('PR14 reuses project revision, structural QA, provider profile, and deterministic report authorities', () => {
  const input = validInput();
  const manifest = core.createUnifiedQaExportManifest(input);

  assert.equal(manifest.projectRevision, input.projectSnapshot.projectRevision);
  assert.equal(manifest.providerProfile.id, 'geckolib4_entity');
  assert.equal(manifest.structuralQa.status, 'PASS');
  assert.deepEqual(manifest.structuralQa.summary, core.validateProject(input.project));
  assert.equal(manifest.report, core.formatReport(core.validateProject(input.project)));
});

test('PR14 derives provider and extension fingerprints from the audited session fingerprint instead of inventing identities', () => {
  const manifest = core.createUnifiedQaExportManifest(validInput());

  assert.deepEqual(manifest.providerFingerprint, {
    activeProviderProfile: 'geckolib4_entity',
    physicalProviders: [{modId: 'geckolib', modVersion: '4.9.2'}],
  });
  assert.deepEqual(manifest.extensionFingerprint, {
    blockbenchVersion: '5.1.6',
    installedExtensions: [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
  });
});

test('PR14 hashes preserved native sources, capture evidence, and staged outputs deterministically', () => {
  const first = core.createUnifiedQaExportManifest(validInput());
  const second = core.createUnifiedQaExportManifest(validInput());

  assert.match(first.sourceArtifacts[0].sha256, /^sha256:[0-9a-f]{64}$/);
  assert.equal(first.sourceArtifacts[0].preserve, true);
  assert.equal(first.sourceArtifacts[0].path.endsWith('.bbmodel'), true);
  assert.match(first.captureEvidence[0].sha256, /^sha256:[0-9a-f]{64}$/);
  assert.match(first.exportArtifacts[0].sha256, /^sha256:[0-9a-f]{64}$/);
  assert.deepEqual(second, first);
});

test('PR14 validates allowlisted export roots and rejects traversal before manifest approval', () => {
  const input = validInput();
  input.exportPlan.outputs[0].relativePath = '../outside/qa_manifest_sample.geo.json';

  assert.throws(
    () => core.createUnifiedQaExportManifest(input),
    error => error?.code === 'EXPORT_PATH_OUTSIDE_ALLOWLISTED_ROOT',
  );
});

test('PR14 emits a deterministic semantic diff over hashed export artifacts', () => {
  const baseline = core.createUnifiedQaExportManifest(validInput());
  const changed = validInput({
    previousExportArtifacts: baseline.exportArtifacts,
    exportPlan: {
      ...validInput().exportPlan,
      outputs: [{
        kind: 'model',
        rootId: 'target_mod_resources',
        relativePath: 'assets/factory/geo/qa_manifest_sample.geo.json',
        content: '{"format_version":"1.21.0"}',
      }, {
        kind: 'texture',
        rootId: 'target_mod_resources',
        relativePath: 'assets/factory/textures/entity/qa_manifest_sample.png',
        content: 'png-v2',
      }],
    },
  });

  const manifest = core.createUnifiedQaExportManifest(changed);
  assert.deepEqual(manifest.semanticDiff.summary, {added: 1, changed: 1, unchanged: 0, removed: 0});
  assert.deepEqual(manifest.semanticDiff.added, ['target_mod_resources:assets/factory/textures/entity/qa_manifest_sample.png']);
  assert.deepEqual(manifest.semanticDiff.changed, ['target_mod_resources:assets/factory/geo/qa_manifest_sample.geo.json']);
});

test('PR14 never marks an asset final merely because staging/export succeeded', () => {
  const manifest = core.createUnifiedQaExportManifest(validInput({
    visualQa: {status: 'PENDING', evidenceId: null, checks: []},
    runtimeQa: {status: 'UNPROVEN', evidenceId: null},
  }));

  assert.equal(manifest.staging.state, 'VALIDATED');
  assert.equal(manifest.exportArtifacts.length, 1);
  assert.equal(manifest.finality.status, 'PENDING');
  assert.ok(manifest.finality.blockers.includes('VISUAL_QA_NOT_PASS'));
  assert.ok(manifest.finality.blockers.includes('RUNTIME_QA_NOT_PASS'));
  assert.equal(manifest.runtimeValidated, false);
  assert.equal(manifest.f4I6Evidence, false);
});

test('PR14 finality requires explicit structural, visual, capture, source, target, staging, runtime, and handoff evidence', () => {
  const manifest = core.createUnifiedQaExportManifest(validInput());

  assert.equal(manifest.finality.status, 'FINAL');
  assert.deepEqual(manifest.finality.blockers, []);
  assert.equal(manifest.runtimeValidated, true);
  assert.equal(manifest.f4I6Evidence, false, 'PR14 manifest finality must not silently satisfy the separate real I6 handoff gate');
  assert.deepEqual(manifest.runtimeTarget, {
    minecraftVersion: '1.21.1', loader: 'neoforge', loaderVersion: '21.1.248', javaVersion: '21',
  });
  assert.deepEqual(manifest.handoffDestinations, [{kind: 'mod_resources', rootId: 'target_mod_resources', namespace: 'factory'}]);
});

test('PR14 standalone bundle exposes the same pure manifest surface', () => {
  assert.equal(typeof standalone.createUnifiedQaExportManifest, 'function');
  assert.equal(standalone.exportAsset, undefined);
  assert.equal(standalone.promoteExport, undefined);
});
