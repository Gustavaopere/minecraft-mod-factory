import test from 'node:test';
import assert from 'node:assert/strict';
import { setTimeout as delay } from 'node:timers/promises';
import { createRequire } from 'node:module';
import WebSocket from 'ws';
import { startBridgeGateway } from '../src/bridge_gateway.mjs';

const require = createRequire(import.meta.url);
const { createBridgeConnection } = require('../../live-bridge/blockbench_bridge_client.js');

function session(ttlMs = 60_000) {
  const now = Date.now();
  return Object.freeze({
    sessionId: 'a'.repeat(32),
    token: 'b'.repeat(64),
    protocolVersion: '1.0.0',
    createdAt: now,
    expiresAt: now + ttlMs,
  });
}

function fingerprint() {
  return {
    minecraft_version: '1.21.1',
    loader: 'neoforge-21.1.248',
    java_version: '21',
    blockbench_version: '5.1.6',
    toolkit_version: '0.3.0',
    protocol_version: '1.0.0',
    installed_extensions: [],
    physical_providers: [],
    active_provider_profile: 'java_block_item',
    project_format: 'free',
    project_revision: 'sha256:test',
  };
}

function router() {
  const calls = [];
  return {
    calls,
    methods: () => ['blockbench.get_status', 'blockbench.get_project'],
    async call(method, params) {
      calls.push({method, params});
      if (method === 'blockbench.get_status') return {connected: true, readOnly: true};
      if (method === 'blockbench.get_project') return {name: 'plugin_asset', projectRevision: 'sha256:test'};
      throw new Error('METHOD_NOT_ALLOWED');
    },
  };
}

test('Blockbench-side bridge client authenticates with the real gateway and routes read-only calls', async (t) => {
  const currentSession = session();
  const gateway = await startBridgeGateway({
    host: '127.0.0.1', port: 0, session: currentSession,
    requestTimeoutMs: 2_000, heartbeatTimeoutMs: 500,
  });
  t.after(() => gateway.close());
  const routed = router();
  const info = gateway.connectionInfo();
  const connection = createBridgeConnection({
    WebSocketClass: WebSocket,
    host: info.host,
    port: info.port,
    session: currentSession,
    fingerprint: fingerprint(),
    router: routed,
    heartbeatIntervalMs: 50,
  });
  t.after(() => connection.disconnect());

  const connected = await connection.connect();
  assert.equal(connected.connected, true);
  assert.equal(connection.status().connected, true);
  assert.deepEqual(connection.status().capabilities.sort(), ['blockbench.get_project', 'blockbench.get_status']);

  assert.deepEqual(await gateway.call('blockbench.get_status', {}), {connected: true, readOnly: true});
  assert.deepEqual(await gateway.call('blockbench.get_project', {}), {name: 'plugin_asset', projectRevision: 'sha256:test'});
  assert.deepEqual(routed.calls.map((entry) => entry.method), ['blockbench.get_status', 'blockbench.get_project']);
});

test('Blockbench-side heartbeat preserves authority and explicit reconnect restores a fresh authenticated socket', async (t) => {
  const currentSession = session();
  const gateway = await startBridgeGateway({
    host: '127.0.0.1', port: 0, session: currentSession,
    requestTimeoutMs: 2_000, heartbeatTimeoutMs: 80,
  });
  t.after(() => gateway.close());
  const info = gateway.connectionInfo();
  const connection = createBridgeConnection({
    WebSocketClass: WebSocket,
    host: info.host,
    port: info.port,
    session: currentSession,
    fingerprint: fingerprint(),
    router: router(),
    heartbeatIntervalMs: 20,
  });
  t.after(() => connection.disconnect());

  await connection.connect();
  await delay(180);
  assert.deepEqual(await gateway.call('blockbench.get_status', {}), {connected: true, readOnly: true});

  const before = connection.status().generation;
  await connection.reconnect();
  const after = connection.status().generation;
  assert.ok(after > before);
  assert.deepEqual(await gateway.call('blockbench.get_project', {}), {name: 'plugin_asset', projectRevision: 'sha256:test'});
});

test('Blockbench-side bridge never advertises non-read-only router methods and returns bounded errors', async (t) => {
  const currentSession = session();
  const gateway = await startBridgeGateway({host: '127.0.0.1', port: 0, session: currentSession});
  t.after(() => gateway.close());
  const info = gateway.connectionInfo();
  const unsafeRouter = {
    methods: () => ['blockbench.get_status', 'model.create_cube'],
    async call() { throw new Error('should never route'); },
  };
  const connection = createBridgeConnection({
    WebSocketClass: WebSocket,
    host: info.host,
    port: info.port,
    session: currentSession,
    fingerprint: fingerprint(),
    router: unsafeRouter,
  });
  t.after(() => connection.disconnect());
  await assert.rejects(connection.connect(), /METHOD_NOT_ALLOWED/);
  assert.equal(connection.status().connected, false);
});
