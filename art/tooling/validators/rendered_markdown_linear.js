'use strict';

function stripMarkdownLinks(value) {
  const source = String(value || '');
  const output = [];
  let index = 0;
  while (index < source.length) {
    const image = source[index] === '!' && source[index + 1] === '[';
    if (!image && source[index] !== '[') {
      output.push(source[index]);
      index += 1;
      continue;
    }

    const open = image ? index + 1 : index;
    const close = source.indexOf(']', open + 1);
    if (close < 0) {
      output.push(source.slice(index));
      break;
    }
    const label = source.slice(open + 1, close);
    const delimiter = source[close + 1];
    if (delimiter === '(') {
      const targetEnd = source.indexOf(')', close + 2);
      if (targetEnd < 0) {
        output.push(source.slice(index));
        break;
      }
      if (targetEnd > close + 2) {
        output.push(label);
        index = targetEnd + 1;
        continue;
      }
    } else if (delimiter === '[') {
      const referenceEnd = source.indexOf(']', close + 2);
      if (referenceEnd < 0) {
        output.push(source.slice(index));
        break;
      }
      output.push(label);
      index = referenceEnd + 1;
      continue;
    }

    output.push(source.slice(index, close + 1));
    index = close + 1;
  }
  return output.join('');
}

function parseFenceOpening(line) {
  const source = String(line || '');
  let index = 0;
  while (index < 3 && source[index] === ' ') index += 1;
  const character = source[index];
  if (character !== '`' && character !== '~') return null;
  let end = index;
  while (source[end] === character) end += 1;
  const length = end - index;
  if (length < 3) return null;
  if (character === '`' && source.slice(end).includes('`')) return null;
  return {character, length};
}

function isHorizontalWhitespace(character) {
  return character === ' ' || character === '\t' || character === '\r' || character === '\f' || character === '\v';
}

function consumeListMarker(source, start, lineEnd) {
  let cursor = start;
  const first = source[cursor];
  if (first === '-' || first === '+' || first === '*') {
    cursor += 1;
  } else {
    let digits = 0;
    while (cursor < lineEnd && digits < 9 && source[cursor] >= '0' && source[cursor] <= '9') {
      cursor += 1;
      digits += 1;
    }
    if (!digits || (source[cursor] !== '.' && source[cursor] !== ')')) return null;
    cursor += 1;
  }
  const whitespaceStart = cursor;
  while (cursor < lineEnd && isHorizontalWhitespace(source[cursor])) cursor += 1;
  return cursor > whitespaceStart ? cursor : null;
}

function hasMarkdownReferenceDefinition(value) {
  const source = String(value || '');
  let lineStart = 0;
  while (lineStart <= source.length) {
    const newline = source.indexOf('\n', lineStart);
    const lineEnd = newline < 0 ? source.length : newline;
    let cursor = lineStart;
    while (cursor < lineEnd && isHorizontalWhitespace(source[cursor])) cursor += 1;

    while (cursor < lineEnd) {
      const afterMarker = consumeListMarker(source, cursor, lineEnd);
      if (afterMarker === null) break;
      cursor = afterMarker;
      while (cursor < lineEnd && isHorizontalWhitespace(source[cursor])) cursor += 1;
    }

    if (source[cursor] === '[') {
      let close = cursor + 1;
      let labelLength = 0;
      while (close < source.length && source[close] !== ']' && labelLength <= 999) {
        close += 1;
        labelLength += 1;
      }
      if (labelLength >= 1 && labelLength <= 999 && source[close] === ']' && source[close + 1] === ':') return true;
    }

    if (newline < 0) break;
    lineStart = newline + 1;
  }
  return false;
}

module.exports = {stripMarkdownLinks, parseFenceOpening, hasMarkdownReferenceDefinition};
