'use strict';

const {READ_ONLY_METHODS, bridgeError} = require('./protocol.js');
const {authorizeRequest} = require('./session_manager.js');

function createGatewayState(options = {}) {
  const session = options.session;
  const now = options.now || Date.now;
  const heartbeatTimeoutMs = Number.isFinite(options.heartbeatTimeoutMs) ? options.heartbeatTimeoutMs : 30_000;
  if (!session || typeof session !== 'object') throw bridgeError('SESSION_MISSING');
  if (!Number.isFinite(session.expiresAt)) throw bridgeError('INVALID_SESSION_EXPIRY');
  if (heartbeatTimeoutMs <= 0) throw bridgeError('INVALID_HEARTBEAT_TIMEOUT');

  let activeConnectionId = null;
  let activeGeneration = 0;
  let lastSeenAt = 0;
  const generations = new Map();

  function validateHandshake(handshake) {
    if (!handshake || handshake.type !== 'handshake') throw bridgeError('INVALID_HANDSHAKE');
    authorizeRequest(session, handshake, {now});
    if (!Array.isArray(handshake.capabilities)) throw bridgeError('INVALID_HANDSHAKE', 'capabilities required');
    if (handshake.capabilities.some((method) => !READ_ONLY_METHODS.includes(method))) throw bridgeError('METHOD_NOT_ALLOWED');
    if (!handshake.fingerprint || typeof handshake.fingerprint !== 'object' || Array.isArray(handshake.fingerprint)) throw bridgeError('INVALID_HANDSHAKE', 'fingerprint required');
  }

  function authenticate(connectionId, handshake) {
    if (typeof connectionId !== 'string' || !connectionId) throw bridgeError('INVALID_CONNECTION_ID');
    validateHandshake(handshake);
    activeGeneration += 1;
    activeConnectionId = connectionId;
    generations.set(connectionId, activeGeneration);
    lastSeenAt = now();
    return {accepted: true, generation: activeGeneration, capabilities: [...handshake.capabilities]};
  }

  function isActive(connectionId) {
    return connectionId === activeConnectionId && generations.get(connectionId) === activeGeneration;
  }

  function isExpired(connectionId) {
    return isActive(connectionId) && now() > session.expiresAt;
  }

  function isTimedOut(connectionId) {
    return isActive(connectionId) && now() - lastSeenAt > heartbeatTimeoutMs;
  }

  function assertActive(connectionId) {
    if (!isActive(connectionId)) throw bridgeError('STALE_CONNECTION');
    if (isExpired(connectionId)) throw bridgeError('SESSION_EXPIRED');
    if (isTimedOut(connectionId)) throw bridgeError('CONNECTION_TIMED_OUT');
    return true;
  }

  function touch(connectionId) {
    assertActive(connectionId);
    lastSeenAt = now();
    return lastSeenAt;
  }

  function invalidate(connectionId) {
    if (isActive(connectionId)) {
      activeConnectionId = null;
      lastSeenAt = 0;
    }
  }

  return Object.freeze({authenticate, isActive, isExpired, isTimedOut, assertActive, touch, invalidate});
}

module.exports = {createGatewayState};
