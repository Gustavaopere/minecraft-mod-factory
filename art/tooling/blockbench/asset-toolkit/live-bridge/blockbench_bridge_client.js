'use strict';

const {assertLoopbackHost, READ_ONLY_METHODS, MAX_MESSAGE_BYTES, bridgeError} = require('./protocol.js');

function assertPort(port) {
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw bridgeError('INVALID_PORT');
  return port;
}

function buildBridgeUrl(options = {}) {
  const host = assertLoopbackHost(options.host);
  const port = assertPort(options.port);
  const authority = host.includes(':') ? `[${host}]` : host;
  return `ws://${authority}:${port}/bridge`;
}

function buildHandshake(options = {}) {
  const session = options.session || {};
  if (typeof session.protocolVersion !== 'string' || typeof session.sessionId !== 'string' || typeof session.token !== 'string') {
    throw bridgeError('INVALID_SESSION');
  }
  const capabilities = Array.isArray(options.capabilities) ? options.capabilities : [];
  if (capabilities.some((method) => !READ_ONLY_METHODS.includes(method))) throw bridgeError('METHOD_NOT_ALLOWED');
  const fingerprint = options.fingerprint && typeof options.fingerprint === 'object' && !Array.isArray(options.fingerprint)
    ? options.fingerprint : {};
  return {
    type: 'handshake',
    protocolVersion: session.protocolVersion,
    sessionId: session.sessionId,
    token: session.token,
    capabilities: [...capabilities],
    fingerprint,
  };
}

function addSocketListener(socket, event, handler) {
  if (socket && typeof socket.addEventListener === 'function') {
    socket.addEventListener(event, handler);
    return () => socket.removeEventListener?.(event, handler);
  }
  if (socket && typeof socket.on === 'function') {
    socket.on(event, handler);
    return () => socket.off?.(event, handler);
  }
  throw bridgeError('WEBSOCKET_API_UNAVAILABLE');
}

async function messageText(eventOrData) {
  let value = eventOrData && typeof eventOrData === 'object' && 'data' in eventOrData
    ? eventOrData.data
    : eventOrData;
  if (typeof value === 'string') return value;
  if (typeof Buffer !== 'undefined' && Buffer.isBuffer && Buffer.isBuffer(value)) return value.toString('utf8');
  if (typeof ArrayBuffer !== 'undefined' && value instanceof ArrayBuffer) return new TextDecoder().decode(new Uint8Array(value));
  if (typeof ArrayBuffer !== 'undefined' && ArrayBuffer.isView?.(value)) {
    return new TextDecoder().decode(new Uint8Array(value.buffer, value.byteOffset, value.byteLength));
  }
  if (value && typeof value.text === 'function') return value.text();
  return String(value);
}

function byteLength(text) {
  if (typeof Buffer !== 'undefined' && Buffer.byteLength) return Buffer.byteLength(text, 'utf8');
  if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(text).byteLength;
  return text.length * 4;
}

function parseBridgeMessage(text) {
  if (byteLength(text) > MAX_MESSAGE_BYTES) throw bridgeError('MESSAGE_TOO_LARGE');
  let value;
  try { value = JSON.parse(text); }
  catch (_) { throw bridgeError('MALFORMED_MESSAGE', 'invalid JSON'); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('MALFORMED_MESSAGE');
  return value;
}

function socketOpenConstant(WebSocketClass) {
  return Number.isInteger(WebSocketClass?.OPEN) ? WebSocketClass.OPEN : 1;
}

function socketClosedConstant(WebSocketClass) {
  return Number.isInteger(WebSocketClass?.CLOSED) ? WebSocketClass.CLOSED : 3;
}

function createBridgeConnection(options = {}) {
  const WebSocketClass = options.WebSocketClass || (typeof globalThis !== 'undefined' ? globalThis.WebSocket : null);
  if (typeof WebSocketClass !== 'function') throw bridgeError('WEBSOCKET_API_UNAVAILABLE');
  const host = options.host;
  const port = options.port;
  const session = options.session || {};
  const fingerprint = options.fingerprint || {};
  const router = options.router;
  const heartbeatIntervalMs = Number.isFinite(options.heartbeatIntervalMs) ? options.heartbeatIntervalMs : 10_000;
  if (!router || typeof router.call !== 'function' || typeof router.methods !== 'function') throw bridgeError('INVALID_ROUTER');
  if (heartbeatIntervalMs <= 0) throw bridgeError('INVALID_HEARTBEAT_INTERVAL');

  const url = buildBridgeUrl({host, port});
  let socket = null;
  let connected = false;
  let connecting = null;
  let generation = 0;
  let capabilities = [];
  let heartbeatTimer = null;
  let intentionalClose = false;
  let listenerCleanup = [];

  function cleanupListeners() {
    for (const remove of listenerCleanup.splice(0)) {
      try { remove(); } catch (_) { /* best effort */ }
    }
  }

  function stopHeartbeat() {
    if (heartbeatTimer) clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }

  function sendJson(target, value) {
    if (!target || target.readyState !== socketOpenConstant(WebSocketClass)) throw bridgeError('BRIDGE_DISCONNECTED');
    const text = JSON.stringify(value);
    if (byteLength(text) > MAX_MESSAGE_BYTES) throw bridgeError('MESSAGE_TOO_LARGE');
    target.send(text);
  }

  function currentStatus() {
    return Object.freeze({
      connected,
      generation,
      capabilities: [...capabilities],
      url,
      protocolVersion: session.protocolVersion || null,
    });
  }

  function validateServerEnvelope(message) {
    if (message.protocolVersion !== session.protocolVersion) throw bridgeError('PROTOCOL_MISMATCH');
    if (message.sessionId !== session.sessionId) throw bridgeError('SESSION_MISMATCH');
  }

  function responseError(error) {
    const code = typeof error?.code === 'string' && error.code ? error.code : 'BLOCKBENCH_ROUTER_ERROR';
    const message = String(error?.message || code).slice(0, 512);
    return {code, message};
  }

  async function handleRequest(target, message) {
    validateServerEnvelope(message);
    if (typeof message.requestId !== 'string' || !message.requestId || message.requestId.length > 128) throw bridgeError('MALFORMED_MESSAGE');
    if (typeof message.method !== 'string' || !READ_ONLY_METHODS.includes(message.method) || !capabilities.includes(message.method)) {
      throw bridgeError('METHOD_NOT_ALLOWED', message.method || 'UNKNOWN');
    }
    const params = message.params === undefined ? {} : message.params;
    if (!params || typeof params !== 'object' || Array.isArray(params)) throw bridgeError('MALFORMED_MESSAGE');
    try {
      const result = await router.call(message.method, params);
      sendJson(target, {
        type: 'response',
        protocolVersion: session.protocolVersion,
        sessionId: session.sessionId,
        requestId: message.requestId,
        ok: true,
        result,
      });
    } catch (error) {
      sendJson(target, {
        type: 'response',
        protocolVersion: session.protocolVersion,
        sessionId: session.sessionId,
        requestId: message.requestId,
        ok: false,
        error: responseError(error),
      });
    }
  }

  function startHeartbeat(target) {
    stopHeartbeat();
    heartbeatTimer = setInterval(() => {
      if (!connected || target !== socket || target.readyState !== socketOpenConstant(WebSocketClass)) return;
      try {
        sendJson(target, {
          type: 'heartbeat',
          protocolVersion: session.protocolVersion,
          sessionId: session.sessionId,
        });
      } catch (_) {
        connected = false;
        stopHeartbeat();
      }
    }, heartbeatIntervalMs);
    heartbeatTimer.unref?.();
  }

  async function connect() {
    if (connected && socket) return currentStatus();
    if (connecting) return connecting;

    capabilities = router.methods();
    if (!Array.isArray(capabilities)) throw bridgeError('INVALID_ROUTER');
    const handshake = buildHandshake({session, capabilities, fingerprint});
    intentionalClose = false;

    connecting = new Promise((resolve, reject) => {
      const target = new WebSocketClass(url);
      socket = target;
      let settled = false;

      const fail = (error) => {
        if (settled) return;
        settled = true;
        connected = false;
        stopHeartbeat();
        connecting = null;
        reject(error instanceof Error ? error : bridgeError('BRIDGE_CONNECTION_FAILED'));
      };

      const onOpen = () => {
        try { sendJson(target, handshake); }
        catch (error) { fail(error); }
      };

      const onMessage = async (event) => {
        let message;
        try {
          message = parseBridgeMessage(await messageText(event));
          if (!connected) {
            if (message.type !== 'handshake_ack') throw bridgeError('INVALID_HANDSHAKE_ACK');
            validateServerEnvelope(message);
            if (!Array.isArray(message.capabilities) || message.capabilities.some((method) => !capabilities.includes(method))) {
              throw bridgeError('CAPABILITY_MISMATCH');
            }
            connected = true;
            generation += 1;
            startHeartbeat(target);
            if (!settled) {
              settled = true;
              connecting = null;
              resolve(currentStatus());
            }
            return;
          }

          if (target !== socket) return;
          if (message.type === 'request') await handleRequest(target, message);
          else if (message.type === 'heartbeat_ack') validateServerEnvelope(message);
          else throw bridgeError('MESSAGE_TYPE_NOT_ALLOWED');
        } catch (error) {
          if (!connected) fail(error);
          else {
            connected = false;
            stopHeartbeat();
            try { target.close(4400, String(error?.code || 'PROTOCOL_ERROR').slice(0, 120)); } catch (_) { /* best effort */ }
          }
        }
      };

      const onClose = () => {
        if (target !== socket) return;
        connected = false;
        stopHeartbeat();
        if (!settled && !intentionalClose) fail(bridgeError('BRIDGE_CONNECTION_CLOSED'));
      };

      const onError = () => {
        if (!settled && !intentionalClose) fail(bridgeError('BRIDGE_CONNECTION_FAILED'));
      };

      listenerCleanup.push(
        addSocketListener(target, 'open', onOpen),
        addSocketListener(target, 'message', onMessage),
        addSocketListener(target, 'close', onClose),
        addSocketListener(target, 'error', onError),
      );
    });

    return connecting;
  }

  async function disconnect() {
    intentionalClose = true;
    connected = false;
    stopHeartbeat();
    const target = socket;
    socket = null;
    connecting = null;
    cleanupListeners();
    if (!target || target.readyState === socketClosedConstant(WebSocketClass)) return;
    try { target.close(1000, 'CLIENT_DISCONNECT'); }
    catch (_) { /* best effort */ }
  }

  async function reconnect() {
    await disconnect();
    return connect();
  }

  return Object.freeze({connect, reconnect, disconnect, status: currentStatus});
}

module.exports = {buildBridgeUrl, buildHandshake, assertPort, createBridgeConnection};
