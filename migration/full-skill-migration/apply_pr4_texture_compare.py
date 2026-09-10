#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ADAPTER = Path("art/tooling/blockbench/asset-toolkit/blockbench-plugin/uv_texture_adapter.js")
AGGREGATE = Path("art/tooling/blockbench/asset-toolkit/asset_toolkit.test.js")

READABLE = '''  function requireComparableTexture(texture) {
    if (texture.layers_enabled === true) {
      fail('LAYERED_TEXTURE_UNSUPPORTED', `Texture "${texture.uuid || texture.id}" uses layers; PR4 requires an explicit future layer target.`);
    }
    const ctx = texture.ctx;
    if (!texture.canvas || !ctx || typeof ctx.getImageData !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', `Texture "${texture.uuid || texture.id}" does not expose a readable 2D canvas.`);
    }
    if (!Number.isSafeInteger(texture.width) || texture.width < 1 || !Number.isSafeInteger(texture.height) || texture.height < 1) {
      fail('INVALID_TEXTURE_DIMENSIONS', `Texture "${texture.uuid || texture.id}" has invalid dimensions.`);
    }
    return texture;
  }

'''

COMPARE = '''  function compareTextures(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      fail('INVALID_TEXTURE_COMPARE', 'Texture compare request must be an object.');
    }
    for (const key of Object.keys(input)) {
      if (key !== 'leftTextureId' && key !== 'rightTextureId') {
        fail('INVALID_TEXTURE_COMPARE', `Texture compare request contains unsupported field "${key}".`);
      }
    }
    const leftTextureId = typeof input.leftTextureId === 'string' ? input.leftTextureId.trim() : '';
    const rightTextureId = typeof input.rightTextureId === 'string' ? input.rightTextureId.trim() : '';
    if (!leftTextureId || !rightTextureId) {
      fail('INVALID_TEXTURE_ID', 'Texture compare requires non-empty leftTextureId and rightTextureId.');
    }

    const left = requireComparableTexture(requireTexture(leftTextureId));
    const right = requireComparableTexture(requireTexture(rightTextureId));
    const leftDimensions = Object.freeze({width: left.width, height: left.height});
    const rightDimensions = Object.freeze({width: right.width, height: right.height});
    const dimensionsEqual = left.width === right.width && left.height === right.height;
    const projectRevision = getRevision();

    if (!dimensionsEqual) {
      return Object.freeze({
        ok: true,
        projectRevision,
        leftTextureId,
        rightTextureId,
        leftDimensions,
        rightDimensions,
        dimensionsEqual: false,
        equal: false,
        comparedPixels: 0,
        changedPixels: null,
        changedBounds: null,
      });
    }

    const comparedPixels = left.width * left.height;
    if (!Number.isSafeInteger(comparedPixels) || comparedPixels > MAX_TEXTURE_PIXELS_PER_BATCH) {
      fail('TEXTURE_PIXEL_BUDGET_EXCEEDED', `Texture compare may read ${comparedPixels} pixels; maximum is ${MAX_TEXTURE_PIXELS_PER_BATCH}.`);
    }
    const leftImage = left.ctx.getImageData(0, 0, left.width, left.height);
    const rightImage = right.ctx.getImageData(0, 0, right.width, right.height);
    const expectedBytes = comparedPixels * 4;
    if (!leftImage?.data || leftImage.data.length !== expectedBytes || !rightImage?.data || rightImage.data.length !== expectedBytes) {
      fail('BLOCKBENCH_API_UNAVAILABLE', 'Texture compare did not receive the expected RGBA bitmap data.');
    }

    let changedPixels = 0;
    let minX = left.width;
    let minY = left.height;
    let maxX = -1;
    let maxY = -1;
    for (let pixelIndex = 0; pixelIndex < comparedPixels; pixelIndex += 1) {
      const offset = pixelIndex * 4;
      let changed = false;
      for (let channel = 0; channel < 4; channel += 1) {
        if (leftImage.data[offset + channel] !== rightImage.data[offset + channel]) {
          changed = true;
          break;
        }
      }
      if (!changed) continue;
      changedPixels += 1;
      const x = pixelIndex % left.width;
      const y = Math.floor(pixelIndex / left.width);
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    }
    const changedBounds = changedPixels === 0 ? null : Object.freeze({
      x: minX,
      y: minY,
      width: maxX - minX + 1,
      height: maxY - minY + 1,
    });

    return Object.freeze({
      ok: true,
      projectRevision,
      leftTextureId,
      rightTextureId,
      leftDimensions,
      rightDimensions,
      dimensionsEqual: true,
      equal: changedPixels === 0,
      comparedPixels,
      changedPixels,
      changedBounds,
    });
  }

'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one marker, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = ADAPTER.read_text(encoding="utf-8")
    if "function compareTextures(input)" in text or "    compareTextures,\n" in text:
        raise SystemExit("compareTextures already exists; refusing duplicate application")

    editable = "  function requireEditableTexture(texture) {\n"
    text = replace_once(text, editable, READABLE + editable, "requireEditableTexture")

    normalized = "  function normalizedTextureRef(value) {\n"
    text = replace_once(text, normalized, COMPARE + normalized, "normalizedTextureRef")

    exported = "  return Object.freeze({\n    getRevision,\n    samplePalette,\n"
    text = replace_once(
        text,
        exported,
        "  return Object.freeze({\n    getRevision,\n    compareTextures,\n    samplePalette,\n",
        "adapter export",
    )
    ADAPTER.write_text(text, encoding="utf-8")

    aggregate = AGGREGATE.read_text(encoding="utf-8")
    acceptance = "require('./asset_toolkit.texture_acceptance.test.js');"
    if acceptance in aggregate:
        raise SystemExit("texture acceptance is already registered in aggregate")
    palette = "require('./asset_toolkit.palette_sampling.test.js');"
    aggregate = replace_once(aggregate, palette, palette + "\n" + acceptance, "aggregate palette")
    AGGREGATE.write_text(aggregate.rstrip("\n") + "\n", encoding="utf-8")

    print("PR4 texture compare implementation applied deterministically")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
