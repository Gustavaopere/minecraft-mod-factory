from __future__ import annotations


class StructuralQAError(ValueError):
    """Raised when C7 cannot safely validate authoritative structural QA inputs."""


def run_structural_qa(build_spec: dict, build_ir: dict, registry: dict | None = None) -> dict:
    raise StructuralQAError("C7 structural QA implementation is not available yet")


def validate_structural_qa_report(report: dict) -> None:
    raise StructuralQAError("C7 structural QA report validation is not available yet")
