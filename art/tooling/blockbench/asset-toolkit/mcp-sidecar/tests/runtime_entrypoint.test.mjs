import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createRuntime, startRuntime, contextFromEnvironment } from '../src/server.mjs';

const require = createRequire(import.meta.url);
const { parseConnectionDescriptor } = require('../../blockbench-plugin/live_bridge_adapter.js');

const context = Object.freeze({
  minecraftVersion: '1.21.1',
  loader: 'neoforge-21.1.248',
  javaVersion: '21',
  activeProviderProfile: 'geckolib4_entity',
  physicalProviders: [{modId: 'geckolib', version: '4.9.2', presence: 'PRESENT', health: 'UNPROVEN'}],
  mcpAuthorizedExtensionIds: ['geckolib'],
});

test('sidecar runtime starts the real loopback gateway and emits a Blockbench-compatible one-time descriptor', async (t) => {
  assert.equal(typeof createRuntime, 'function');
  const runtime = await createRuntime({host: '127.0.0.1', port: 0, context});
  t.after(() => runtime.close());

  const descriptor = runtime.descriptor;
  assert.equal(descriptor.host, '127.0.0.1');
  assert.ok(Number.isInteger(descriptor.port) && descriptor.port > 0);
  assert.match(descriptor.sessionId, /^[0-9a-f]{32}$/);
  assert.match(descriptor.token, /^[0-9a-f]{64}$/);
  assert.equal(descriptor.protocolVersion, '1.0.0');
  assert.equal(descriptor.minecraftVersion, '1.21.1');
  assert.equal(descriptor.activeProviderProfile, 'geckolib4_entity');
  assert.equal('url' in descriptor, false);
  assert.equal('path' in descriptor, false);
  assert.deepEqual(parseConnectionDescriptor(JSON.stringify(descriptor)), descriptor);
  await assert.rejects(runtime.callBridge('blockbench.get_status', {}), /BRIDGE_UNAVAILABLE/);
});

test('runtime context rejects malformed provider identities and extension allowlist entries', () => {
  assert.throws(
    () => contextFromEnvironment({RPG_ASSET_PHYSICAL_PROVIDERS_JSON: '[{}]'}),
    /INVALID_RUNTIME_CONTEXT/,
  );
  assert.throws(
    () => contextFromEnvironment({RPG_ASSET_MCP_EXTENSIONS_JSON: '[""]'}),
    /INVALID_RUNTIME_CONTEXT/,
  );
});

test('startRuntime injects the live gateway call into stdio serving and transfers the descriptor exactly once', async () => {
  let descriptorCount = 0;
  let suppliedCallBridge = null;
  await startRuntime({
    host: '127.0.0.1',
    port: 0,
    context,
    onDescriptor(descriptor) {
      descriptorCount += 1;
      parseConnectionDescriptor(descriptor);
    },
    async serveStdioFn(options) {
      suppliedCallBridge = options.callBridge;
      assert.equal(typeof suppliedCallBridge, 'function');
    },
  });
  assert.equal(descriptorCount, 1);
  assert.equal(typeof suppliedCallBridge, 'function');
});
