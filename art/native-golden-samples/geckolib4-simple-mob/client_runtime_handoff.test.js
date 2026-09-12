'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;
const CLIENT_CONTRACT = path.join(ROOT, 'runtime-smoke', 'client-contract.json');
const CLIENT_PROOF_SOURCE = path.join(
  ROOT,
  'runtime-smoke',
  'tests',
  'GoldenSampleMobClientRuntimeProof.java',
);
const PREPARER = path.join(ROOT, 'runtime-smoke', 'tests', 'prepare_client_proof.py');
const RUNNER = path.join(ROOT, 'runtime-smoke', 'tests', 'run_live_client_proof.sh');
const WORKFLOW = path.join(
  ROOT,
  '..',
  '..',
  '..',
  '.github',
  'workflows',
  'factory-art-geckolib4-native-golden.yml',
);

test('live-client proof contract is target-exact and wired to a real client run', () => {
  assert.equal(
    fs.existsSync(CLIENT_CONTRACT),
    true,
    'live-client runtime contract is required before F4/I6 can advance',
  );

  const contract = JSON.parse(fs.readFileSync(CLIENT_CONTRACT, 'utf8'));
  assert.deepEqual(contract.target, {
    minecraft: '1.21.1',
    neoforge: '21.1.248',
    java: 21,
    geckolib: '4.9.2',
  });
  assert.deepEqual(contract.connection, {
    host: '127.0.0.1',
    port: 25565,
    mechanism: 'ConnectScreen.startConnecting@StartupReadyScreen',
    startupScreens: ['TitleScreen', 'AccessibilityOnboardingScreen'],
  });
  assert.deepEqual(contract.expectedEvidence, [
    'renderer_invoked',
    'baked_model_observed',
    'texture_resolved',
    'animation_motion_observed',
  ]);

  assert.equal(
    fs.existsSync(CLIENT_PROOF_SOURCE),
    true,
    'client runtime proof fixture is required',
  );
  assert.equal(fs.existsSync(PREPARER), true, 'client proof preparer is required');
  assert.equal(fs.existsSync(RUNNER), true, 'client proof runner is required');

  const workflow = fs.readFileSync(WORKFLOW, 'utf8');
  const proofSource = fs.readFileSync(CLIENT_PROOF_SOURCE, 'utf8');
  const preparer = fs.readFileSync(PREPARER, 'utf8');
  const runner = fs.readFileSync(RUNNER, 'utf8');
  assert.match(workflow, /runtime-smoke\/tests\/prepare_client_proof\.py/);
  assert.match(workflow, /runtime-smoke\/tests\/run_live_client_proof\.sh/);
  assert.match(runner, /runClient/);
  assert.match(proofSource, /ClientTickEvent\.Post/);
  assert.match(proofSource, /TitleScreen/);
  assert.match(proofSource, /AccessibilityOnboardingScreen/);
  assert.match(proofSource, /ConnectScreen\.startConnecting/);
  assert.match(preparer, /GoldenSampleMobClientRuntimeProof::onClientTick/);
  assert.doesNotMatch(preparer, /--quickPlayMultiplayer/);
  assert.doesNotMatch(runner, /quickPlayArgument/);
});
