'use strict';

const PROTOCOL_VERSION = '1.0.0';
const MAX_MESSAGE_BYTES = 64 * 1024;

const READ_ONLY_METHODS = Object.freeze([
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
]);

const READ_ONLY_METHOD_SET = new Set(READ_ONLY_METHODS);

function bridgeError(code, message = code) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  return error;
}

function assertLoopbackHost(host) {
  if (host === '::1') return host;
  if (typeof host === 'string') {
    const parts = host.split('.');
    if (parts.length === 4 && parts[0] === '127' && parts.every((part) => /^\d{1,3}$/.test(part) && Number(part) >= 0 && Number(part) <= 255)) return host;
  }
  throw bridgeError('LOOPBACK_REQUIRED', 'bridge transport must bind to a numeric loopback address');
}

function validateEnvelope(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('MALFORMED_MESSAGE');
  for (const key of ['protocolVersion', 'sessionId', 'token', 'requestId', 'method']) {
    if (typeof value[key] !== 'string' || !value[key]) throw bridgeError('MALFORMED_MESSAGE', `missing ${key}`);
  }
  if (!/^[0-9a-f]{32}$/i.test(value.sessionId)) throw bridgeError('MALFORMED_MESSAGE', 'invalid sessionId');
  if (!/^[0-9a-f]{64}$/i.test(value.token)) throw bridgeError('MALFORMED_MESSAGE', 'invalid token');
  if (value.requestId.length > 128) throw bridgeError('MALFORMED_MESSAGE', 'requestId too long');
  if (!READ_ONLY_METHOD_SET.has(value.method)) throw bridgeError('METHOD_NOT_ALLOWED', value.method);
  if (value.params === undefined) value.params = {};
  if (!value.params || typeof value.params !== 'object' || Array.isArray(value.params)) throw bridgeError('MALFORMED_MESSAGE', 'params must be an object');
  return value;
}

function parseEnvelope(raw) {
  const text = Buffer.isBuffer(raw) ? raw.toString('utf8') : String(raw);
  if (Buffer.byteLength(text, 'utf8') > MAX_MESSAGE_BYTES) throw bridgeError('MESSAGE_TOO_LARGE');
  let value;
  try { value = JSON.parse(text); }
  catch (_) { throw bridgeError('MALFORMED_MESSAGE', 'invalid JSON'); }
  return validateEnvelope(value);
}

module.exports = {
  PROTOCOL_VERSION,
  MAX_MESSAGE_BYTES,
  READ_ONLY_METHODS,
  bridgeError,
  assertLoopbackHost,
  validateEnvelope,
  parseEnvelope,
};
