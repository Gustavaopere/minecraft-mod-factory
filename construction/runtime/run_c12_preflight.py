from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from construction.runtime.c12_evidence import C12EvidenceError, package_evidence
from construction.runtime.c12_runtime_acceptance import (
    C12Error,
    FINGERPRINT_KEYS,
    TARGET,
    build_runtime_acceptance_report,
    validate_i5_manifest,
)

SYNTHETIC_FIXTURE_AUTHORITY = "SYNTHETIC_PREFLIGHT_ONLY"
DEFAULT_OUTPUT = Path("build/c12-runtime-acceptance/preflight-report.json")
FINAL_PHYSICAL_REPORT = Path(
    "construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json"
)
PREFLIGHT_STAGES = {
    "target_environment": "PASS",
    "i5_baseline": "PASS",
    "client_smoke": "DEFERRED",
    "live_placement": "DEFERRED",
    "runtime_visual_fidelity": "DEFERRED",
    "multiplayer": "DEFERRED",
    "full_modpack": "DEFERRED",
    "evidence_packaging": "PASS",
}


def _load_json(path: Path, label: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise C12Error(f"{label} must be a regular non-symlink file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise C12Error(f"{label} is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise C12Error(f"{label} must contain a JSON object")
    return value


def _evidence_paths(evidence_root: Path) -> list[Path]:
    if evidence_root.is_symlink() or not evidence_root.is_dir():
        raise C12Error("evidence root must be an existing non-symlink directory")
    paths = [path for path in evidence_root.rglob("*") if path.is_file() or path.is_symlink()]
    if not paths:
        raise C12Error("preflight evidence root must contain at least one file")
    return sorted(paths, key=lambda path: path.as_posix())


def run_preflight(
    *,
    i5_manifest_path: Path,
    blocker_state_path: Path,
    evidence_root: Path,
) -> dict[str, object]:
    """Build C12 preflight evidence without executing or claiming physical acceptance."""
    i5_manifest = _load_json(Path(i5_manifest_path), "I5 preflight manifest")
    if i5_manifest.get("fixture_authority") != SYNTHETIC_FIXTURE_AUTHORITY:
        raise C12Error(
            "C12 preflight I5 fixture must be explicitly marked SYNTHETIC_PREFLIGHT_ONLY"
        )
    i5_errors = validate_i5_manifest(i5_manifest)
    if i5_errors:
        raise C12Error("I5 preflight manifest rejected: " + "; ".join(i5_errors))

    blocker_state = _load_json(Path(blocker_state_path), "Construction final blocker state")
    blocker = {
        "status": blocker_state.get("status"),
        "blocks_c12_acceptance": blocker_state.get("blocks_c12_acceptance"),
    }

    try:
        evidence = package_evidence(Path(evidence_root), _evidence_paths(Path(evidence_root)))
    except C12EvidenceError as exc:
        raise C12Error(f"C12 preflight evidence rejected: {exc}") from exc

    fingerprints = {key: None for key in FINGERPRINT_KEYS}
    return build_runtime_acceptance_report(
        mode="PREFLIGHT",
        target=TARGET,
        blocker=blocker,
        authority_fingerprints=fingerprints,
        stages=PREFLIGHT_STAGES,
        evidence=evidence,
        diagnostics=[
            "synthetic preflight evidence only; no physical runtime acceptance is claimed"
        ],
    )


def _safe_output_path(repo_root: Path, requested: Path) -> Path:
    candidate = requested if requested.is_absolute() else repo_root / requested
    try:
        relative = candidate.relative_to(repo_root)
    except ValueError as exc:
        raise C12Error("preflight output path must remain inside the repository workspace") from exc
    if any(part in {"..", "."} for part in relative.parts):
        raise C12Error("preflight output path must be canonical inside the repository workspace")
    if relative == FINAL_PHYSICAL_REPORT:
        raise C12Error("preflight runner must not write the final physical C12 report path")

    current = repo_root
    for part in relative.parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise C12Error("preflight output path contains a symlink component")
    if candidate.exists() and candidate.is_symlink():
        raise C12Error("preflight output file must not be a symlink")

    resolved_parent = candidate.parent.resolve()
    if not resolved_parent.is_relative_to(repo_root.resolve()):
        raise C12Error("preflight output parent escapes repository workspace")
    return candidate


def _write_report(repo_root: Path, output: Path, report: dict[str, object]) -> None:
    destination = _safe_output_path(repo_root, output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Run Construction C12 preflight orchestration")
    parser.add_argument("--i5-manifest", type=Path, required=True)
    parser.add_argument("--blocker-state", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    def rooted(path: Path) -> Path:
        return path if path.is_absolute() else repo_root / path

    try:
        report = run_preflight(
            i5_manifest_path=rooted(args.i5_manifest),
            blocker_state_path=rooted(args.blocker_state),
            evidence_root=rooted(args.evidence_root),
        )
        _write_report(repo_root, args.output, report)
    except (C12Error, OSError) as exc:
        print(f"C12_PREFLIGHT_BLOCKED: {exc}")
        return 2

    print(
        "C12 preflight: "
        f"{report['overall_readiness']} / acceptance={report['overall_acceptance']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
