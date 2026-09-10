'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const adapter = require('./blockbench-plugin/live_bridge_adapter.js');

function descriptor(overrides = {}) {
  return {
    host: '127.0.0.1',
    port: 39123,
    sessionId: 'a'.repeat(32),
    token: 'b'.repeat(64),
    protocolVersion: '1.0.0',
    minecraftVersion: '1.21.1',
    loader: 'neoforge-21.1.248',
    javaVersion: '21',
    physicalProviders: [
      {modId: 'geckolib', version: '4.9.2', presence: 'PRESENT', health: 'UNPROVEN'},
    ],
    activeProviderProfile: 'geckolib4_entity',
    mcpAuthorizedExtensionIds: ['geckolib'],
    heartbeatIntervalMs: 1000,
    ...overrides,
  };
}

function project() {
  return {
    name: 'adapter_asset',
    save_path: 'C:/Users/private/models/adapter_asset.bbmodel',
    format: {id: 'free'},
    groups: [{name: 'root', uuid: 'root', origin: [0, 0, 0], parent: null}],
    elements: [],
    textures: [],
    animations: [],
    selected_elements: [],
  };
}

function blockbench({isWeb = false} = {}) {
  return {
    Blockbench: {
      isWeb,
      version: '5.1.6',
      Project: project(),
    },
    Plugins: {
      installed: [
        {id: 'geckolib', version: '4.2.5', source: 'store', disabled: false},
        {id: 'disabled_plugin', version: '1.0.0', source: 'store', disabled: true},
        {id: 'no_version', source: 'store', disabled: false},
      ],
    },
  };
}

class DummyWebSocket {}

test('connection descriptor is strict, bounded and never echoes the session token in validation errors', () => {
  const parsed = adapter.parseConnectionDescriptor(JSON.stringify(descriptor()));
  assert.equal(parsed.host, '127.0.0.1');
  assert.equal(parsed.port, 39123);
  assert.equal(parsed.protocolVersion, '1.0.0');

  const secret = 'f'.repeat(64);
  for (const bad of [
    descriptor({token: secret, unexpected: true}),
    descriptor({token: 'not-hex'}),
    descriptor({sessionId: 'short'}),
    descriptor({protocolVersion: '99.0.0'}),
  ]) {
    let error = null;
    try { adapter.parseConnectionDescriptor(bad); } catch (caught) { error = caught; }
    assert.ok(error instanceof Error);
    assert.equal(String(error.message).includes(secret), false, 'connection secret leaked through validation error');
  }
});

test('installed extension fingerprint uses Blockbench current installed state and excludes disabled or incomplete entries', () => {
  assert.deepEqual(adapter.installedExtensions(blockbench()), [
    {pluginId: 'geckolib', pluginVersion: '4.2.5'},
  ]);
});

test('live bridge runtime is desktop-only and fails closed in Blockbench web', () => {
  assert.throws(
    () => adapter.createBlockbenchLiveBridgeRuntime(blockbench({isWeb: true}), descriptor(), {WebSocketClass: DummyWebSocket}),
    /DESKTOP_REQUIRED/,
  );
});

test('desktop runtime fingerprints actual editor state, preserves provider authority and exposes no secret in status', async () => {
  const input = descriptor();
  const runtime = adapter.createBlockbenchLiveBridgeRuntime(blockbench(), input, {WebSocketClass: DummyWebSocket});

  assert.equal(runtime.fingerprint.blockbench_version, '5.1.6');
  assert.equal(runtime.fingerprint.minecraft_version, '1.21.1');
  assert.deepEqual(runtime.fingerprint.installed_extensions, [
    {pluginId: 'geckolib', pluginVersion: '4.2.5'},
  ]);
  assert.deepEqual(runtime.fingerprint.physical_providers, [
    {modId: 'geckolib', modVersion: '4.9.2'},
  ]);
  assert.equal(JSON.stringify(runtime.fingerprint).includes(input.token), false);
  assert.equal(JSON.stringify(runtime.connection.status()).includes(input.token), false);
  assert.equal(runtime.connection.status().url.includes(input.token), false);

  const resolved = await runtime.router.call('blockbench.profiles.resolve_for_asset', {profileId: 'geckolib4_entity'});
  assert.equal(resolved.status, 'AVAILABLE');
  assert.equal(resolved.profile.id, 'geckolib4_entity');

  const snapshot = await runtime.router.call('blockbench.get_project', {});
  assert.equal(snapshot.sourceFile, 'adapter_asset.bbmodel');
  assert.ok(snapshot.projectRevision.startsWith('sha256:'));
  assert.equal(JSON.stringify(snapshot).includes('C:/Users/private'), false);
});

test('desktop runtime rejects non-loopback connection descriptors before opening a socket', () => {
  assert.throws(
    () => adapter.createBlockbenchLiveBridgeRuntime(blockbench(), descriptor({host: '192.168.1.20'}), {WebSocketClass: DummyWebSocket}),
    /LOOPBACK_REQUIRED/,
  );
});
