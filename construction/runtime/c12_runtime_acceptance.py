from __future__ import annotations

import copy
import re
from typing import Any

TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}
FINAL_BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
MODES = frozenset({"PREFLIGHT", "PHYSICAL_ACCEPTANCE"})
STAGE_IDS = (
    "target_environment",
    "i5_baseline",
    "client_smoke",
    "live_placement",
    "runtime_visual_fidelity",
    "multiplayer",
    "full_modpack",
    "evidence_packaging",
)
STAGE_STATES = frozenset({"PASS", "FAIL", "BLOCKED", "DEFERRED", "NOT_APPLICABLE"})
FINGERPRINT_KEYS = (
    "i2_physical_snapshot_sha256",
    "c4_registry_sha256",
    "c11_manifest_sha256",
    "c6_schematic_sha256",
    "c7_report_sha256",
    "c8_report_sha256",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_I5_SUITE_IDS = ("unit", "gametest", "dedicated_server")
_I5_SUITE_STATES = frozenset({"PASS", "BLOCKED"})


class C12Error(RuntimeError):
    """Raised when C12 cannot safely construct a runtime-acceptance report."""


def _is_exact_target(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != set(TARGET):
        return False
    if isinstance(value.get("java"), bool):
        return False
    return value == TARGET


def _validate_fingerprints(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["authority_fingerprints must be an object"]
    errors: list[str] = []
    if set(value) != set(FINGERPRINT_KEYS):
        errors.append("authority_fingerprints keys must match the C12 contract")
        return errors
    for key in FINGERPRINT_KEYS:
        fingerprint = value[key]
        if fingerprint is not None and (
            not isinstance(fingerprint, str) or _SHA256_RE.fullmatch(fingerprint) is None
        ):
            errors.append(f"authority_fingerprints.{key} must be null or lowercase sha256")
    return errors


def _validate_stages(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["stages must be an object"]
    errors: list[str] = []
    if set(value) != set(STAGE_IDS):
        errors.append("stage ids must match the C12 contract")
        return errors
    for stage_id in STAGE_IDS:
        state = value[stage_id]
        if not isinstance(state, str) or state not in STAGE_STATES:
            errors.append(f"invalid stage state for {stage_id}: {state!r}")
    return errors


def _active_blocker(blocker: object) -> tuple[bool, str | None]:
    if not isinstance(blocker, dict):
        raise C12Error("blocker must be an object")
    if set(blocker) != {"status", "blocks_c12_acceptance"}:
        raise C12Error("blocker fields must match the C12 contract")
    status = blocker["status"]
    blocks = blocker["blocks_c12_acceptance"]
    if status is not None and not isinstance(status, str):
        raise C12Error("blocker.status must be a string or null")
    if not isinstance(blocks, bool):
        raise C12Error("blocker.blocks_c12_acceptance must be boolean")
    active = status == FINAL_BLOCKER and blocks is True
    if blocks is True and status != FINAL_BLOCKER:
        raise C12Error("blocking C12 acceptance requires the exact final blocker")
    return active, status if active else None


def validate_i5_manifest(manifest: object) -> list[str]:
    """Validate the subset of the canonical Engineering I5 manifest consumed by C12."""
    if not isinstance(manifest, dict):
        return ["I5 manifest must be an object"]

    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("I5 schema_version must be 1")
    if not _is_exact_target(manifest.get("target")):
        errors.append(f"I5 target must equal {TARGET}")

    suites = manifest.get("suites")
    suite_states: list[str] = []
    if not isinstance(suites, list):
        errors.append("I5 suites must be a list")
    else:
        ids: list[str] = []
        for index, suite in enumerate(suites):
            if not isinstance(suite, dict):
                errors.append(f"I5 suites[{index}] must be an object")
                continue
            suite_id = suite.get("suite_id")
            state = suite.get("state")
            if not isinstance(suite_id, str):
                errors.append(f"I5 suites[{index}].suite_id must be a string")
            else:
                ids.append(suite_id)
            if not isinstance(state, str) or state not in _I5_SUITE_STATES:
                errors.append(f"I5 suites[{index}].state must be PASS or BLOCKED")
            else:
                suite_states.append(state)
        if ids != list(_I5_SUITE_IDS):
            errors.append("I5 suite ids must be unit, gametest, dedicated_server in canonical order")

    overall = manifest.get("overall_state")
    if overall not in _I5_SUITE_STATES:
        errors.append("I5 overall_state must be PASS or BLOCKED")
    elif len(suite_states) == len(_I5_SUITE_IDS):
        expected = "PASS" if all(state == "PASS" for state in suite_states) else "BLOCKED"
        if overall != expected:
            errors.append(f"I5 overall_state must be {expected} for the supplied suite states")

    return errors


def build_runtime_acceptance_report(
    *,
    mode: str,
    target: object,
    blocker: object,
    authority_fingerprints: object,
    stages: object,
    evidence: list[dict[str, str]] | None = None,
    diagnostics: list[str] | None = None,
) -> dict[str, object]:
    """Build one deterministic C12 report without promoting preflight to acceptance."""
    if mode not in MODES:
        raise C12Error(f"invalid mode: {mode!r}")
    if not _is_exact_target(target):
        raise C12Error(f"target drift rejected: expected {TARGET}, got {target}")

    fingerprint_errors = _validate_fingerprints(authority_fingerprints)
    if fingerprint_errors:
        raise C12Error("; ".join(fingerprint_errors))
    stage_errors = _validate_stages(stages)
    if stage_errors:
        raise C12Error("; ".join(stage_errors))
    blocker_is_active, blocker_name = _active_blocker(blocker)

    canonical_stages = {stage_id: stages[stage_id] for stage_id in STAGE_IDS}  # type: ignore[index]
    canonical_fingerprints = {
        key: authority_fingerprints[key] for key in FINGERPRINT_KEYS  # type: ignore[index]
    }

    if evidence is None:
        canonical_evidence: list[dict[str, str]] = []
    elif isinstance(evidence, list) and all(isinstance(item, dict) for item in evidence):
        canonical_evidence = copy.deepcopy(evidence)
    else:
        raise C12Error("evidence must be a list of objects")

    if diagnostics is None:
        canonical_diagnostics: list[str] = []
    elif isinstance(diagnostics, list) and all(isinstance(item, str) for item in diagnostics):
        canonical_diagnostics = list(diagnostics)
    else:
        raise C12Error("diagnostics must be a list of strings")

    has_failure = any(state == "FAIL" for state in canonical_stages.values())
    all_pass = all(state == "PASS" for state in canonical_stages.values())
    all_physical_fingerprints = all(
        isinstance(canonical_fingerprints[key], str)
        and _SHA256_RE.fullmatch(canonical_fingerprints[key]) is not None  # type: ignore[arg-type]
        for key in FINGERPRINT_KEYS
    )

    if has_failure:
        overall_readiness = "BLOCKED"
        overall_acceptance = "FAIL"
    elif mode == "PREFLIGHT":
        overall_readiness = "PREFLIGHT_READY"
        overall_acceptance = "BLOCKED"
    elif blocker_is_active:
        overall_readiness = "PREFLIGHT_READY"
        overall_acceptance = "BLOCKED"
    elif all_pass and all_physical_fingerprints:
        overall_readiness = "PREFLIGHT_READY"
        overall_acceptance = "PASS"
    else:
        overall_readiness = "PREFLIGHT_READY"
        overall_acceptance = "BLOCKED"

    report: dict[str, object] = {
        "schema_version": 1,
        "mode": mode,
        "target": copy.deepcopy(TARGET),
        "authority_fingerprints": canonical_fingerprints,
        "stages": canonical_stages,
        "blocker": blocker_name,
        "overall_readiness": overall_readiness,
        "overall_acceptance": overall_acceptance,
        "evidence": canonical_evidence,
        "diagnostics": canonical_diagnostics,
    }

    report_errors = validate_runtime_acceptance_report(report)
    if report_errors:
        raise C12Error("constructed invalid report: " + "; ".join(report_errors))
    return report


def validate_runtime_acceptance_report(report: object) -> list[str]:
    """Return deterministic validation errors for a C12 report."""
    if not isinstance(report, dict):
        return ["report must be an object"]

    errors: list[str] = []
    expected_keys = {
        "schema_version",
        "mode",
        "target",
        "authority_fingerprints",
        "stages",
        "blocker",
        "overall_readiness",
        "overall_acceptance",
        "evidence",
        "diagnostics",
    }
    if set(report) != expected_keys:
        errors.append("report fields must match the C12 contract")
        return errors

    if report.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if report.get("mode") not in MODES:
        errors.append("mode is invalid")
    if not _is_exact_target(report.get("target")):
        errors.append(f"target must equal {TARGET}")
    errors.extend(_validate_fingerprints(report.get("authority_fingerprints")))
    errors.extend(_validate_stages(report.get("stages")))

    blocker = report.get("blocker")
    if blocker not in {None, FINAL_BLOCKER}:
        errors.append("blocker must be null or the exact final blocker")
    if report.get("overall_readiness") not in {"PREFLIGHT_READY", "BLOCKED"}:
        errors.append("overall_readiness is invalid")
    if report.get("overall_acceptance") not in {"PASS", "FAIL", "BLOCKED"}:
        errors.append("overall_acceptance is invalid")

    evidence = report.get("evidence")
    if not isinstance(evidence, list) or any(not isinstance(item, dict) for item in evidence):
        errors.append("evidence must be a list of objects")
    diagnostics = report.get("diagnostics")
    if not isinstance(diagnostics, list) or any(not isinstance(item, str) for item in diagnostics):
        errors.append("diagnostics must be a list of strings")

    if not errors:
        stages = report["stages"]
        mode = report["mode"]
        acceptance = report["overall_acceptance"]
        if mode == "PREFLIGHT" and acceptance == "PASS":
            errors.append("PREFLIGHT cannot have final acceptance PASS")
        if blocker == FINAL_BLOCKER and acceptance == "PASS":
            errors.append("active final blocker cannot have acceptance PASS")
        if any(state == "FAIL" for state in stages.values()) and acceptance != "FAIL":
            errors.append("a failed stage requires overall acceptance FAIL")

    return errors
