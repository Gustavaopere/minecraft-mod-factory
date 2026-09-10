'use strict';

const crypto = require('node:crypto');
const {PROTOCOL_VERSION, bridgeError} = require('./protocol.js');

function compareText(left, right) {
  const leftText = String(left);
  const rightText = String(right);
  const localized = leftText.localeCompare(rightText, 'en', {sensitivity: 'variant', numeric: false});
  if (localized !== 0) return localized;
  if (leftText < rightText) return -1;
  if (leftText > rightText) return 1;
  return 0;
}
function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort(compareText).map((key) => [key, stable(value[key])]));
  return value;
}

function requestHash(request) {
  return crypto.createHash('sha256').update(JSON.stringify(stable({method: request.method, params: request.params || {}}))).digest('hex');
}

function createSession(options = {}) {
  const randomBytes = options.randomBytes || crypto.randomBytes;
  const now = options.now || Date.now;
  const ttlMs = Number.isFinite(options.ttlMs) ? options.ttlMs : 15 * 60 * 1000;
  if (ttlMs <= 0) throw bridgeError('INVALID_SESSION_TTL');
  return Object.freeze({
    sessionId: Buffer.from(randomBytes(16)).toString('hex'),
    token: Buffer.from(randomBytes(32)).toString('hex'),
    createdAt: now(),
    expiresAt: now() + ttlMs,
    protocolVersion: PROTOCOL_VERSION,
  });
}

function secureEqual(left, right) {
  if (typeof left !== 'string' || typeof right !== 'string') return false;
  const a = Buffer.from(left, 'utf8');
  const b = Buffer.from(right, 'utf8');
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

function authorizeRequest(session, envelope, options = {}) {
  const now = options.now || Date.now;
  if (!session || typeof session !== 'object') throw bridgeError('SESSION_MISSING');
  if (envelope.protocolVersion !== session.protocolVersion) throw bridgeError('PROTOCOL_MISMATCH');
  if (now() > session.expiresAt) throw bridgeError('SESSION_EXPIRED');
  if (!secureEqual(envelope.sessionId, session.sessionId)) throw bridgeError('SESSION_MISMATCH');
  if (!secureEqual(envelope.token, session.token)) throw bridgeError('AUTH_FAILED');
  return {authorized: true, sessionId: session.sessionId};
}

function createRequestLedger() {
  const entries = new Map();
  return Object.freeze({
    async execute(request, executor) {
      if (!request || typeof request.requestId !== 'string' || !request.requestId) throw bridgeError('REQUEST_ID_REQUIRED');
      const hash = requestHash(request);
      const prior = entries.get(request.requestId);
      if (prior) {
        if (prior.hash !== hash) throw bridgeError('REPLAY_CONFLICT');
        return prior.promise;
      }
      const promise = Promise.resolve().then(executor);
      entries.set(request.requestId, {hash, promise});
      try { return await promise; }
      catch (error) { entries.delete(request.requestId); throw error; }
    },
    clear() { entries.clear(); },
    size() { return entries.size; },
  });
}

module.exports = {createSession, authorizeRequest, createRequestLedger, requestHash};
