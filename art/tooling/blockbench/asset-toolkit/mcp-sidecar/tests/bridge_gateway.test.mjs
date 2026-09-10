import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import WebSocket from 'ws';
import { Client, InMemoryTransport } from '@modelcontextprotocol/client';
import { startBridgeGateway } from '../src/bridge_gateway.mjs';
import { createServer } from '../src/server.mjs';

const session = Object.freeze({
  sessionId: '1'.repeat(32),
  token: '2'.repeat(64),
  protocolVersion: '1.0.0',
  createdAt: 1_000,
  expiresAt: Date.now() + 60_000,
});

function handshake(overrides = {}) {
  return {
    type: 'handshake',
    protocolVersion: session.protocolVersion,
    sessionId: session.sessionId,
    token: session.token,
    capabilities: ['blockbench.get_status', 'blockbench.get_project'],
    fingerprint: {minecraft_version: '1.21.1', project_revision: 'sha256:test'},
    ...overrides,
  };
}

async function openSocket(url, hello = handshake()) {
  const socket = new WebSocket(url, {perMessageDeflate: false});
  await once(socket, 'open');
  socket.send(JSON.stringify(hello));
  const [raw] = await once(socket, 'message');
  const ack = JSON.parse(raw.toString());
  assert.equal(ack.type, 'handshake_ack');
  assert.equal(ack.protocolVersion, session.protocolVersion);
  return socket;
}

async function nextJson(socket) {
  const [raw] = await once(socket, 'message');
  return JSON.parse(raw.toString());
}

test('real loopback WebSocket gateway authenticates and correlates read-only request/response', async (t) => {
  const gateway = await startBridgeGateway({host: '127.0.0.1', port: 0, session, requestTimeoutMs: 2_000, heartbeatTimeoutMs: 10_000});
  t.after(() => gateway.close());
  const info = gateway.connectionInfo();
  assert.equal(info.host, '127.0.0.1');
  assert.ok(Number.isInteger(info.port) && info.port > 0);
  assert.equal(info.path, '/bridge');
  assert.equal(info.token, session.token);
  const socket = await openSocket(info.url);
  t.after(() => socket.close());

  const pending = gateway.call('blockbench.get_status', {});
  const request = await nextJson(socket);
  assert.equal(request.type, 'request');
  assert.equal(request.method, 'blockbench.get_status');
  assert.equal(request.sessionId, session.sessionId);
  assert.equal('token' in request, false);
  socket.send(JSON.stringify({
    type: 'response', protocolVersion: session.protocolVersion, sessionId: session.sessionId,
    requestId: request.requestId, ok: true, result: {connected: true, readOnly: true},
  }));
  assert.deepEqual(await pending, {connected: true, readOnly: true});
});

test('reconnect supersedes the old socket and late old-socket responses have no authority', async (t) => {
  const gateway = await startBridgeGateway({host: '127.0.0.1', port: 0, session, requestTimeoutMs: 2_000, heartbeatTimeoutMs: 10_000});
  t.after(() => gateway.close());
  const first = await openSocket(gateway.connectionInfo().url);
  const second = await openSocket(gateway.connectionInfo().url);
  t.after(() => first.close());
  t.after(() => second.close());

  const [closeCode] = await once(first, 'close');
  assert.equal(closeCode, 4409);
  const pending = gateway.call('blockbench.get_project', {});
  const request = await nextJson(second);
  first.send?.(JSON.stringify({type: 'response', protocolVersion: session.protocolVersion, sessionId: session.sessionId, requestId: request.requestId, ok: true, result: {stale: true}}));
  second.send(JSON.stringify({type: 'response', protocolVersion: session.protocolVersion, sessionId: session.sessionId, requestId: request.requestId, ok: true, result: {name: 'fresh'}}));
  assert.deepEqual(await pending, {name: 'fresh'});
});

test('invalid handshake is rejected and unavailable/timeout states fail closed', async (t) => {
  const gateway = await startBridgeGateway({host: '127.0.0.1', port: 0, session, requestTimeoutMs: 50, heartbeatTimeoutMs: 10_000});
  t.after(() => gateway.close());
  await assert.rejects(gateway.call('blockbench.get_status', {}), /BRIDGE_UNAVAILABLE/);

  const bad = new WebSocket(gateway.connectionInfo().url, {perMessageDeflate: false});
  await once(bad, 'open');
  bad.send(JSON.stringify(handshake({token: '0'.repeat(64)})));
  const [code] = await once(bad, 'close');
  assert.equal(code, 4401);

  const socket = await openSocket(gateway.connectionInfo().url);
  t.after(() => socket.close());
  const timed = gateway.call('blockbench.get_status', {});
  await nextJson(socket);
  await assert.rejects(timed, /BRIDGE_REQUEST_TIMEOUT/);
});

test('an authenticated connection loses authority when the ephemeral session expires', async (t) => {
  let now = 1_000;
  const expiringSession = Object.freeze({...session, createdAt: now, expiresAt: 1_500});
  const gateway = await startBridgeGateway({
    host: '127.0.0.1', port: 0, session: expiringSession,
    now: () => now, requestTimeoutMs: 50, heartbeatTimeoutMs: 10_000,
  });
  t.after(() => gateway.close());
  const socket = await openSocket(gateway.connectionInfo().url, handshake());
  t.after(() => socket.close());

  now = 1_501;
  await assert.rejects(gateway.call('blockbench.get_status', {}), /SESSION_EXPIRED/);
});

test('MCP client -> official server -> WebSocket gateway -> Blockbench response is end-to-end read-only', async (t) => {
  const gateway = await startBridgeGateway({host: '127.0.0.1', port: 0, session, requestTimeoutMs: 2_000, heartbeatTimeoutMs: 10_000});
  t.after(() => gateway.close());
  const socket = await openSocket(gateway.connectionInfo().url);
  t.after(() => socket.close());

  const server = createServer({callBridge: gateway.call});
  const client = new Client({name: 'rpg-asset-test-client', version: '1.0.0'});
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await Promise.all([server.connect(serverTransport), client.connect(clientTransport)]);
  t.after(async () => { await client.close(); await server.close(); });

  const listed = await client.listTools();
  assert.equal(listed.tools.length, 20);
  assert.ok(listed.tools.every((tool) => tool.annotations?.readOnlyHint === true && tool.annotations?.destructiveHint === false));

  const call = client.callTool({name: 'blockbench.get_status', arguments: {}});
  const request = await nextJson(socket);
  socket.send(JSON.stringify({
    type: 'response', protocolVersion: session.protocolVersion, sessionId: session.sessionId,
    requestId: request.requestId, ok: true, result: {connected: true, readOnly: true, projectRevision: 'sha256:abc'},
  }));
  const result = await call;
  assert.deepEqual(result.structuredContent, {connected: true, readOnly: true, projectRevision: 'sha256:abc'});
});
