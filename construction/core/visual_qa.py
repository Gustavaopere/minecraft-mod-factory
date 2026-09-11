from __future__ import annotations


class VisualQAError(ValueError):
    pass


def run_visual_qa(
    build_spec: dict,
    build_ir: dict,
    views: dict[str, bytes],
    structural_report: dict | None = None,
    palette_resolution: dict | None = None,
    review_evidence: dict | None = None,
) -> dict:
    raise VisualQAError("C8 visual QA implementation is not available yet")


def validate_visual_qa_report(report: dict) -> None:
    raise VisualQAError("C8 visual QA implementation is not available yet")
