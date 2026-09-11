from __future__ import annotations


class PreviewRenderError(ValueError):
    pass


def render_canonical_views(build_ir: dict) -> dict[str, bytes]:
    raise PreviewRenderError("C8 preview renderer implementation is not available yet")
