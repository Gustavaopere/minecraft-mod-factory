'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const protocol = require('./live-bridge/protocol.js');
const sessionManager = require('./live-bridge/session_manager.js');
const fingerprint = require('./live-bridge/fingerprint.js');
const snapshots = require('./live-bridge/project_snapshot.js');
const routerModule = require('./live-bridge/read_only_router.js');

const EXPECTED_READ_ONLY_METHODS = [
  'blockbench.get_status',
  'blockbench.get_capabilities',
  'blockbench.get_project',
  'blockbench.get_scene_graph',
  'blockbench.get_selection',
  'blockbench.get_bones',
  'blockbench.get_elements',
  'blockbench.get_textures',
  'blockbench.get_animations',
  'blockbench.get_animation',
  'blockbench.compute_bounds',
  'blockbench.validate',
  'blockbench.validate_contract',
  'blockbench.extensions.list',
  'blockbench.extensions.get',
  'blockbench.extensions.get_fingerprint',
  'blockbench.extensions.check_compatibility',
  'blockbench.profiles.list',
  'blockbench.profiles.get',
  'blockbench.profiles.resolve_for_asset',
];

test('PR2 protocol exposes only the approved read-only observability surface', () => {
  assert.deepEqual([...protocol.READ_ONLY_METHODS].sort(), [...EXPECTED_READ_ONLY_METHODS].sort());
  for (const forbidden of [
    'blockbench.execute_script',
    'blockbench.extensions.install_arbitrary',
    'blockbench.extensions.load_url',
    'blockbench.extensions.execute_action_by_name',
    'model.create_cube',
    'texture.paint_region',
  ]) assert.equal(protocol.READ_ONLY_METHODS.includes(forbidden), false, forbidden);
});

test('bridge transport accepts numeric loopback only and rejects public or ambiguous hosts', () => {
  assert.equal(protocol.assertLoopbackHost('127.0.0.1'), '127.0.0.1');
  assert.equal(protocol.assertLoopbackHost('127.23.4.5'), '127.23.4.5');
  assert.equal(protocol.assertLoopbackHost('::1'), '::1');
  for (const host of ['0.0.0.0', '192.168.1.5', '8.8.8.8', 'localhost', 'example.com', '::']) {
    assert.throws(() => protocol.assertLoopbackHost(host), /LOOPBACK_REQUIRED/);
  }
});

test('session uses ephemeral credentials and rejects stale, wrong-session, wrong-token and wrong-protocol requests', () => {
  let byte = 0;
  const randomBytes = (length) => Buffer.from(Array.from({length}, () => (byte++ % 251) + 1));
  const session = sessionManager.createSession({randomBytes, now: () => 1_000, ttlMs: 60_000});
  assert.match(session.sessionId, /^[0-9a-f]{32}$/);
  assert.match(session.token, /^[0-9a-f]{64}$/);
  assert.equal(session.expiresAt, 61_000);

  const envelope = {
    protocolVersion: protocol.PROTOCOL_VERSION,
    sessionId: session.sessionId,
    token: session.token,
    requestId: 'req-1',
    method: 'blockbench.get_status',
    params: {},
  };
  assert.equal(sessionManager.authorizeRequest(session, envelope, {now: () => 2_000}).authorized, true);
  assert.throws(() => sessionManager.authorizeRequest(session, {...envelope, sessionId: '0'.repeat(32)}, {now: () => 2_000}), /SESSION_MISMATCH/);
  assert.throws(() => sessionManager.authorizeRequest(session, {...envelope, token: '0'.repeat(64)}, {now: () => 2_000}), /AUTH_FAILED/);
  assert.throws(() => sessionManager.authorizeRequest(session, {...envelope, protocolVersion: '99.0.0'}, {now: () => 2_000}), /PROTOCOL_MISMATCH/);
  assert.throws(() => sessionManager.authorizeRequest(session, envelope, {now: () => 61_001}), /SESSION_EXPIRED/);
});

test('read-only request ledger replays identical requests and rejects request-id payload conflicts', async () => {
  const ledger = sessionManager.createRequestLedger();
  let calls = 0;
  const executor = async () => ({value: ++calls});
  const request = {requestId: 'req-stable', method: 'blockbench.get_status', params: {}};
  assert.deepEqual(await ledger.execute(request, executor), {value: 1});
  assert.deepEqual(await ledger.execute(request, executor), {value: 1});
  assert.equal(calls, 1);
  await assert.rejects(
    ledger.execute({...request, params: {different: true}}, executor),
    /REPLAY_CONFLICT/,
  );
});

test('request hashing is independent of insertion order for Unicode-normalization-equivalent keys', async () => {
  const composed = '\u00e9';
  const decomposed = 'e\u0301';
  const firstParams = {[composed]: 'composed', [decomposed]: 'decomposed'};
  const secondParams = {[decomposed]: 'decomposed', [composed]: 'composed'};
  const first = {requestId: 'req-unicode-order', method: 'blockbench.get_status', params: firstParams};
  const second = {requestId: 'req-unicode-order', method: 'blockbench.get_status', params: secondParams};

  assert.equal(sessionManager.requestHash(first), sessionManager.requestHash(second));

  const ledger = sessionManager.createRequestLedger();
  let calls = 0;
  const executor = async () => ({value: ++calls});
  assert.deepEqual(await ledger.execute(first, executor), {value: 1});
  assert.deepEqual(await ledger.execute(second, executor), {value: 1});
  assert.equal(calls, 1);
});

test('session fingerprint is complete, bounded to supplied evidence and never contains bridge secrets', () => {
  const result = fingerprint.buildSessionFingerprint({
    minecraftVersion: '1.21.1', loader: 'neoforge-21.1.248', javaVersion: '21',
    blockbenchVersion: '5.1.6', toolkitVersion: '0.3.0', protocolVersion: protocol.PROTOCOL_VERSION,
    installedExtensions: [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
    physicalProviders: [{modId: 'geckolib', modVersion: '4.9.2'}],
    activeProviderProfile: 'geckolib4_entity', projectFormat: 'geckolib_model', projectRevision: 'sha256:abc',
    token: 'must-not-leak', sessionId: 'must-not-leak',
  });
  assert.deepEqual(Object.keys(result).sort(), [
    'active_provider_profile', 'blockbench_version', 'installed_extensions', 'java_version', 'loader',
    'minecraft_version', 'physical_providers', 'project_format', 'project_revision', 'protocol_version', 'toolkit_version',
  ].sort());
  assert.equal(JSON.stringify(result).includes('must-not-leak'), false);
});

test('project snapshot revision is deterministic, changes with project state and redacts absolute source paths', () => {
  const base = {
    name: 'bridge_asset', save_path: 'C:/Users/private/models/bridge_asset.bbmodel', format: {id: 'free'},
    groups: [{name: 'root', uuid: 'root', origin: [0,0,0], parent: null}],
    elements: [], textures: [], animations: [], selected_elements: [],
  };
  const first = snapshots.createProjectSnapshot(base);
  const second = snapshots.createProjectSnapshot({...base});
  const changed = snapshots.createProjectSnapshot({...base, groups: [...base.groups, {name: 'arm', uuid: 'arm', origin: [0,1,0], parent: null}]});
  assert.equal(first.projectRevision, second.projectRevision);
  assert.notEqual(first.projectRevision, changed.projectRevision);
  assert.equal(JSON.stringify(first).includes('C:/Users/private'), false);
  assert.equal(first.sourceFile, 'bridge_asset.bbmodel');
});

test('read-only router exposes project observability and reuses provider/extension authority from PR1', async () => {
  const project = {
    name: 'router_asset', save_path: '/private/router_asset.bbmodel', format: {id: 'free'},
    groups: [{name: 'root', uuid: 'root', origin: [0,0,0], parent: null}],
    elements: [], textures: [], animations: [], selected_elements: [],
  };
  const router = routerModule.createReadOnlyRouter({
    getProject: () => project,
    getBlockbenchVersion: () => '5.1.6',
    getInstalledExtensions: () => [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
    physicalProviders: {geckolib: {modId: 'geckolib', version: '4.9.2', presence: 'PRESENT', health: 'UNPROVEN'}},
    activeProviderProfile: () => 'geckolib4_entity',
  });
  const status = await router.call('blockbench.get_status', {});
  assert.equal(status.connected, true);
  assert.equal(status.readOnly, true);
  assert.ok(status.projectRevision.startsWith('sha256:'));
  const profiles = await router.call('blockbench.profiles.list', {});
  assert.ok(profiles.some((entry) => entry.id === 'geckolib4_entity'));
  const extensions = await router.call('blockbench.extensions.list', {});
  assert.ok(extensions.some((entry) => entry.pluginId === 'geckolib'));
  await assert.rejects(router.call('model.create_cube', {}), /METHOD_NOT_ALLOWED/);
  await assert.rejects(router.call('blockbench.execute_script', {}), /METHOD_NOT_ALLOWED/);
});

test('protocol parser rejects malformed and oversized envelopes before routing', () => {
  const good = JSON.stringify({
    protocolVersion: protocol.PROTOCOL_VERSION,
    sessionId: '1'.repeat(32), token: '2'.repeat(64), requestId: 'req-2',
    method: 'blockbench.get_status', params: {},
  });
  assert.equal(protocol.parseEnvelope(good).method, 'blockbench.get_status');
  assert.throws(() => protocol.parseEnvelope('{not json'), /MALFORMED_MESSAGE/);
  assert.throws(() => protocol.parseEnvelope('x'.repeat(protocol.MAX_MESSAGE_BYTES + 1)), /MESSAGE_TOO_LARGE/);
  assert.throws(() => protocol.parseEnvelope(JSON.stringify({...JSON.parse(good), method: 'model.create_cube'})), /METHOD_NOT_ALLOWED/);
});
