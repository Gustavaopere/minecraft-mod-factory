import { once } from 'node:events';
import { randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import { WebSocketServer, WebSocket } from 'ws';

const require = createRequire(import.meta.url);
const {
  READ_ONLY_METHODS,
  MAX_MESSAGE_BYTES,
  assertLoopbackHost,
  bridgeError,
} = require('../../live-bridge/protocol.js');
const { createGatewayState } = require('../../live-bridge/gateway_protocol.js');

const BRIDGE_PATH = '/bridge';
const READ_ONLY_METHOD_SET = new Set(READ_ONLY_METHODS);

function assertListenPort(port) {
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw bridgeError('INVALID_PORT');
  return port;
}

function assertPositiveTimeout(value, fallback, code) {
  const result = Number.isFinite(value) ? value : fallback;
  if (result <= 0) throw bridgeError(code);
  return result;
}

function jsonMessage(raw) {
  const size = Buffer.isBuffer(raw) ? raw.length : Buffer.byteLength(String(raw), 'utf8');
  if (size > MAX_MESSAGE_BYTES) throw bridgeError('MESSAGE_TOO_LARGE');
  let value;
  try {
    value = JSON.parse(Buffer.isBuffer(raw) ? raw.toString('utf8') : String(raw));
  } catch (_) {
    throw bridgeError('MALFORMED_MESSAGE', 'invalid JSON');
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('MALFORMED_MESSAGE');
  return value;
}

function endpointUrl(host, port) {
  const authority = host.includes(':') ? `[${host}]` : host;
  return `ws://${authority}:${port}${BRIDGE_PATH}`;
}

function closeQuietly(socket, code, reason) {
  if (!socket || socket.readyState === WebSocket.CLOSED) return;
  try {
    socket.close(code, String(reason || '').slice(0, 120));
  } catch (_) {
    try { socket.terminate(); } catch (_) { /* best effort */ }
  }
}

function responseError(message) {
  const code = typeof message?.error?.code === 'string' && message.error.code
    ? message.error.code
    : 'BLOCKBENCH_REQUEST_FAILED';
  const detail = typeof message?.error?.message === 'string' && message.error.message
    ? message.error.message
    : code;
  return bridgeError(code, detail);
}

function closeCodeFor(error, fallback = 4400) {
  if (error?.code === 'SESSION_EXPIRED' || error?.code === 'AUTH_FAILED' || error?.code === 'SESSION_MISMATCH') return 4401;
  if (error?.code === 'CONNECTION_TIMED_OUT' || error?.code === 'BRIDGE_HEARTBEAT_TIMEOUT') return 4408;
  return fallback;
}

export async function startBridgeGateway(options = {}) {
  const host = assertLoopbackHost(options.host || '127.0.0.1');
  const port = assertListenPort(options.port ?? 0);
  const session = options.session;
  const now = options.now || Date.now;
  const requestTimeoutMs = assertPositiveTimeout(options.requestTimeoutMs, 10_000, 'INVALID_REQUEST_TIMEOUT');
  const heartbeatTimeoutMs = assertPositiveTimeout(options.heartbeatTimeoutMs, 30_000, 'INVALID_HEARTBEAT_TIMEOUT');
  const handshakeTimeoutMs = assertPositiveTimeout(options.handshakeTimeoutMs, 5_000, 'INVALID_HANDSHAKE_TIMEOUT');
  const state = createGatewayState({session, now, heartbeatTimeoutMs});

  const server = new WebSocketServer({
    host,
    port,
    path: BRIDGE_PATH,
    perMessageDeflate: false,
    maxPayload: MAX_MESSAGE_BYTES,
    clientTracking: true,
  });
  await once(server, 'listening');

  const address = server.address();
  if (!address || typeof address === 'string' || !Number.isInteger(address.port)) {
    await new Promise((resolve) => server.close(resolve));
    throw bridgeError('BRIDGE_LISTEN_FAILED');
  }
  const boundPort = address.port;

  let active = null;
  let closed = false;
  const pending = new Map();

  function rejectPendingFor(connectionId, error) {
    for (const [requestId, entry] of pending) {
      if (entry.connectionId !== connectionId) continue;
      clearTimeout(entry.timer);
      pending.delete(requestId);
      entry.reject(error);
    }
  }

  function clearActive(connectionId, error) {
    if (!active || active.connectionId !== connectionId) return;
    state.invalidate(connectionId);
    rejectPendingFor(connectionId, error || bridgeError('BRIDGE_UNAVAILABLE'));
    active = null;
  }

  function acceptResponse(connectionId, message) {
    if (!state.isActive(connectionId)) return;
    state.touch(connectionId);
    if (message.protocolVersion !== session.protocolVersion || message.sessionId !== session.sessionId) return;
    if (typeof message.requestId !== 'string' || !message.requestId) return;
    const entry = pending.get(message.requestId);
    if (!entry || entry.connectionId !== connectionId) return;
    clearTimeout(entry.timer);
    pending.delete(message.requestId);
    if (message.ok === true) entry.resolve(message.result);
    else entry.reject(responseError(message));
  }

  function acceptHeartbeat(connectionId, socket, message) {
    if (!state.isActive(connectionId)) return;
    if (message.protocolVersion !== session.protocolVersion || message.sessionId !== session.sessionId) return;
    state.touch(connectionId);
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'heartbeat_ack',
        protocolVersion: session.protocolVersion,
        sessionId: session.sessionId,
      }));
    }
  }

  server.on('connection', (socket, request) => {
    const remoteAddressRaw = request?.socket?.remoteAddress || '';
    const remoteAddress = remoteAddressRaw.startsWith('::ffff:') ? remoteAddressRaw.slice(7) : remoteAddressRaw;
    try {
      assertLoopbackHost(remoteAddress);
    } catch (_) {
      closeQuietly(socket, 4403, 'LOOPBACK_REQUIRED');
      return;
    }

    const connectionId = randomUUID();
    let authenticated = false;
    const handshakeTimer = setTimeout(() => closeQuietly(socket, 4401, 'HANDSHAKE_TIMEOUT'), handshakeTimeoutMs);
    handshakeTimer.unref?.();

    socket.on('message', (raw, isBinary) => {
      if (isBinary) {
        closeQuietly(socket, 4400, 'TEXT_MESSAGES_ONLY');
        return;
      }

      let message;
      try {
        message = jsonMessage(raw);
      } catch (error) {
        closeQuietly(socket, 4400, error?.code || 'MALFORMED_MESSAGE');
        return;
      }

      if (!authenticated) {
        try {
          const result = state.authenticate(connectionId, message);
          const previous = active;
          authenticated = true;
          clearTimeout(handshakeTimer);
          active = {
            connectionId,
            generation: result.generation,
            socket,
            capabilities: new Set(result.capabilities),
          };
          socket.send(JSON.stringify({
            type: 'handshake_ack',
            protocolVersion: session.protocolVersion,
            sessionId: session.sessionId,
            generation: result.generation,
            capabilities: result.capabilities,
          }));

          if (previous && previous.connectionId !== connectionId) {
            rejectPendingFor(previous.connectionId, bridgeError('BRIDGE_RECONNECTED'));
            setImmediate(() => closeQuietly(previous.socket, 4409, 'SUPERSEDED'));
          }
        } catch (error) {
          clearTimeout(handshakeTimer);
          closeQuietly(socket, 4401, error?.code || 'AUTH_FAILED');
        }
        return;
      }

      try {
        if (!state.isActive(connectionId)) return;
        if (message.type === 'response') acceptResponse(connectionId, message);
        else if (message.type === 'heartbeat') acceptHeartbeat(connectionId, socket, message);
        else throw bridgeError('MESSAGE_TYPE_NOT_ALLOWED');
      } catch (error) {
        clearActive(connectionId, error);
        closeQuietly(socket, closeCodeFor(error), error?.code || 'PROTOCOL_ERROR');
      }
    });

    socket.on('close', () => {
      clearTimeout(handshakeTimer);
      clearActive(connectionId, bridgeError('BRIDGE_DISCONNECTED'));
    });

    socket.on('error', () => {
      clearActive(connectionId, bridgeError('BRIDGE_DISCONNECTED'));
    });
  });

  const heartbeatWatch = setInterval(() => {
    if (!active) return;
    if (state.isExpired(active.connectionId)) {
      const expired = active;
      clearActive(expired.connectionId, bridgeError('SESSION_EXPIRED'));
      closeQuietly(expired.socket, 4401, 'SESSION_EXPIRED');
      return;
    }
    if (!state.isTimedOut(active.connectionId)) return;
    const stale = active;
    clearActive(stale.connectionId, bridgeError('BRIDGE_HEARTBEAT_TIMEOUT'));
    closeQuietly(stale.socket, 4408, 'HEARTBEAT_TIMEOUT');
  }, Math.max(25, Math.min(1_000, Math.floor(heartbeatTimeoutMs / 2))));
  heartbeatWatch.unref?.();

  async function call(method, params = {}) {
    if (closed || !active) throw bridgeError('BRIDGE_UNAVAILABLE');
    if (!READ_ONLY_METHOD_SET.has(method)) throw bridgeError('METHOD_NOT_ALLOWED', method);
    if (!params || typeof params !== 'object' || Array.isArray(params)) throw bridgeError('MALFORMED_MESSAGE', 'params must be an object');

    const connection = active;
    try {
      state.assertActive(connection.connectionId);
    } catch (error) {
      clearActive(connection.connectionId, error);
      closeQuietly(connection.socket, closeCodeFor(error, 4408), error?.code || 'BRIDGE_UNAVAILABLE');
      throw error;
    }
    if (!connection.capabilities.has(method)) throw bridgeError('BRIDGE_CAPABILITY_UNAVAILABLE', method);
    if (connection.socket.readyState !== WebSocket.OPEN) {
      clearActive(connection.connectionId, bridgeError('BRIDGE_UNAVAILABLE'));
      throw bridgeError('BRIDGE_UNAVAILABLE');
    }

    const requestId = randomUUID();
    const request = {
      type: 'request',
      protocolVersion: session.protocolVersion,
      sessionId: session.sessionId,
      requestId,
      method,
      params,
    };

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        const entry = pending.get(requestId);
        if (!entry) return;
        pending.delete(requestId);
        reject(bridgeError('BRIDGE_REQUEST_TIMEOUT', method));
      }, requestTimeoutMs);
      timer.unref?.();
      pending.set(requestId, {connectionId: connection.connectionId, resolve, reject, timer});

      try {
        connection.socket.send(JSON.stringify(request), (error) => {
          if (!error) return;
          const entry = pending.get(requestId);
          if (!entry) return;
          clearTimeout(entry.timer);
          pending.delete(requestId);
          reject(bridgeError('BRIDGE_SEND_FAILED', error.message));
        });
      } catch (error) {
        clearTimeout(timer);
        pending.delete(requestId);
        reject(bridgeError('BRIDGE_SEND_FAILED', error?.message || 'send failed'));
      }
    });
  }

  function connectionInfo() {
    return Object.freeze({
      host,
      port: boundPort,
      path: BRIDGE_PATH,
      url: endpointUrl(host, boundPort),
      sessionId: session.sessionId,
      token: session.token,
      protocolVersion: session.protocolVersion,
    });
  }

  async function close() {
    if (closed) return;
    closed = true;
    clearInterval(heartbeatWatch);
    for (const entry of pending.values()) {
      clearTimeout(entry.timer);
      entry.reject(bridgeError('BRIDGE_CLOSED'));
    }
    pending.clear();
    if (active) state.invalidate(active.connectionId);
    active = null;
    for (const client of server.clients) {
      try { client.terminate(); } catch (_) { /* best effort */ }
    }
    await new Promise((resolve) => server.close(resolve));
  }

  return Object.freeze({call, connectionInfo, close});
}
