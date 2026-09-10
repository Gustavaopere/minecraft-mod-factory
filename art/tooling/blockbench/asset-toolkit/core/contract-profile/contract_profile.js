'use strict';

function parseProfileJson(text) {
  const value = typeof text === 'string' ? text.trim() : '';
  if (!value) return {};
  const parsed = JSON.parse(value);
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Profile must be a JSON object.');
  return parsed;
}

module.exports = {parseProfileJson};
