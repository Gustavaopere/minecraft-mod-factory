'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;

function load(relative) { return require(path.join(ROOT, relative)); }

function sessionFixture() {
  return {sessionId: '1'.repeat(32), token: '2'.repeat(64), protocolVersion: '1.0.0', createdAt: 1_000, expiresAt: 61_000};
}

test('plugin bridge URL contains numeric loopback endpoint but never embeds the session token', () => {
  const client = load('live-bridge/blockbench_bridge_client.js');
  const session = sessionFixture();
  const url = client.buildBridgeUrl({host: '127.0.0.1', port: 24873});
  assert.equal(url, 'ws://127.0.0.1:24873/bridge');
  assert.equal(url.includes(session.token), false);
  assert.throws(() => client.buildBridgeUrl({host: '0.0.0.0', port: 24873}), /LOOPBACK_REQUIRED/);
  assert.throws(() => client.buildBridgeUrl({host: '127.0.0.1', port: 0}), /INVALID_PORT/);
});

test('plugin handshake carries explicit protocol, session, capability and fingerprint evidence', () => {
  const client = load('live-bridge/blockbench_bridge_client.js');
  const session = sessionFixture();
  const message = client.buildHandshake({
    session,
    capabilities: ['blockbench.get_status', 'blockbench.get_project'],
    fingerprint: {minecraft_version: '1.21.1', project_revision: 'sha256:abc'},
  });
  assert.deepEqual(message, {
    type: 'handshake', protocolVersion: '1.0.0', sessionId: session.sessionId, token: session.token,
    capabilities: ['blockbench.get_status', 'blockbench.get_project'],
    fingerprint: {minecraft_version: '1.21.1', project_revision: 'sha256:abc'},
  });
});

test('gateway authentication rejects stale credentials and reconnect invalidates the previous socket', () => {
  const gateway = load('live-bridge/gateway_protocol.js');
  const session = sessionFixture();
  let now = 2_000;
  const state = gateway.createGatewayState({session, now: () => now, heartbeatTimeoutMs: 10_000});
  const handshake = {type: 'handshake', protocolVersion: '1.0.0', sessionId: session.sessionId, token: session.token, capabilities: ['blockbench.get_status'], fingerprint: {}};
  const first = state.authenticate('socket-1', handshake);
  assert.equal(first.accepted, true);
  assert.equal(state.isActive('socket-1'), true);
  const second = state.authenticate('socket-2', handshake);
  assert.equal(second.accepted, true);
  assert.equal(state.isActive('socket-1'), false);
  assert.equal(state.isActive('socket-2'), true);
  assert.throws(() => state.assertActive('socket-1'), /STALE_CONNECTION/);
  assert.throws(() => state.authenticate('socket-3', {...handshake, token: '0'.repeat(64)}), /AUTH_FAILED/);
  now = 62_000;
  assert.throws(() => state.authenticate('socket-4', handshake), /SESSION_EXPIRED/);
});

test('gateway heartbeat timeout closes authority without accepting late responses', () => {
  const gateway = load('live-bridge/gateway_protocol.js');
  const session = sessionFixture();
  let now = 2_000;
  const state = gateway.createGatewayState({session, now: () => now, heartbeatTimeoutMs: 5_000});
  const handshake = {type: 'handshake', protocolVersion: '1.0.0', sessionId: session.sessionId, token: session.token, capabilities: ['blockbench.get_status'], fingerprint: {}};
  state.authenticate('socket-1', handshake);
  state.touch('socket-1');
  now = 7_001;
  assert.equal(state.isTimedOut('socket-1'), true);
  assert.throws(() => state.assertActive('socket-1'), /CONNECTION_TIMED_OUT/);
});

test('sidecar package pins the audited stable MCP v2 SDK and WebSocket dependencies', () => {
  const packagePath = path.join(ROOT, 'mcp-sidecar', 'package.json');
  const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  assert.equal(pkg.private, true);
  assert.equal(pkg.type, 'module');
  assert.equal(pkg.dependencies['@modelcontextprotocol/server'], '2.0.0');
  assert.equal(pkg.dependencies.ws, '8.21.3');
  assert.equal(pkg.dependencies.zod, '4.5.4');
  assert.equal(pkg.devDependencies['@modelcontextprotocol/client'], '2.0.0');
  assert.match(pkg.engines.node, />=22/);
});

test('MCP sidecar manifest maps the exact PR2 read-only methods and no mutation tools', () => {
  const protocol = load('live-bridge/protocol.js');
  const manifest = load('mcp-sidecar/tool_manifest.cjs');
  assert.deepEqual(manifest.TOOL_NAMES.slice().sort(), protocol.READ_ONLY_METHODS.slice().sort());
  for (const name of manifest.TOOL_NAMES) assert.match(name, /^blockbench\./);
  for (const forbidden of ['model.create_cube', 'texture.paint_region', 'blockbench.execute_script']) assert.equal(manifest.TOOL_NAMES.includes(forbidden), false);
});

test('sidecar source uses official MCP stdio server entry and never exposes HTTP or arbitrary execution', () => {
  const serverSource = fs.readFileSync(path.join(ROOT, 'mcp-sidecar', 'src', 'server.mjs'), 'utf8');
  assert.match(serverSource, /@modelcontextprotocol\/server/);
  assert.match(serverSource, /@modelcontextprotocol\/server\/stdio/);
  assert.match(serverSource, /serveStdio/);
  assert.equal(/execute_script|child_process|\beval\s*\(|new Function|exec\s*\(|spawn\s*\(/.test(serverSource), false);
  assert.equal(/StreamableHTTP|createMcpHandler|listen\s*\(.*0\.0\.0\.0/.test(serverSource), false);
});
