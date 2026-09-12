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

  const workflow = fs.readFileSync(WORKFLOW, 'utf8');
  assert.match(workflow, /runClient/);
  assert.match(workflow, /--quickPlayMultiplayer/);
});
