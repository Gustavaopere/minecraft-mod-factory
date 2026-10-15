#!/usr/bin/env python3
"""Opt-in, fail-closed I10 live late-neighbor diagnostic (not a multiplayer gate)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_i10_chunk_acceptance import ServerSession

PARTIAL_ADD = "forceload add 159 160 161 160"
CASING_ADD = "forceload add 159 159 161 159"
FULL_ADD = "forceload add 159 159 161 161"
FULL_REMOVE = "forceload remove 159 159 161 161"
OUTPUT_RELATIVE = Path("build/i10-delayed-neighbor-diagnostic")


class DiagnosticBlocked(RuntimeError):
    pass


class DiagnosticSession(ServerSession):
    """Only this disposable diagnostic may send the two extra bounded commands."""

    def send(self, command, expected_action=None, marker_prefix="I10_PROBE "):
        if command in {PARTIAL_ADD, CASING_ADD}:
            if expected_action is not None or marker_prefix != "I10_PROBE ":
                raise DiagnosticBlocked("PENDING: staged chunk commands cannot request a marker")
            if self.process is None or self.process.poll() is not None or self.process.stdin is None:
                raise DiagnosticBlocked("PENDING: diagnostic server is not writable")
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            return None
        return super().send(command, expected_action, marker_prefix)


def _run_diagnostic_phase(project, output, phase, body):
    session = DiagnosticSession(project, phase)
    try:
        session.start()
        return body(session)
    finally:
        try:
            session.stop_gracefully()
        finally:
            session.force_cleanup()
            session.write_log(output)


def is_pending_casing_gap(marker: dict[str, object], revision: int) -> bool:
    """Port remains loaded/bound, controller is pending, so an extra casing chunk is missing."""
    return (
        marker["validation"] == "UNAVAILABLE"
        and marker["runtime"] == "PENDING_REVALIDATION"
        and marker["revision"] == revision
        and marker["last_known_formed"] is True
        and marker["controller_visual"] is False
        and marker["port_visual"] is False
        and marker["port_bound"] is True
    )


def _formed_pre_probe(marker: dict[str, object], revision: int) -> bool:
    return (
        marker["validation"] == "VALID"
        and marker["runtime"] == "FORMED"
        and marker["revision"] == revision
        and marker["last_known_formed"] is True
        and marker["controller_visual"] is True
        and marker["port_visual"] is True
        and marker["port_bound"] is True
    )


def verify_staged_neighbor_liveness(session, revision: int) -> dict[str, object]:
    """Require an observed real UNAVAILABLE period before restoring the casing chunks.

    Uses only read-only 'i10probe peek' until AFTER visual/binding recovery.
    A missing chunk condition that cannot be reproduced must fail closed.
    """
    session.send(PARTIAL_ADD)
    initial = session.poll_peek(
        lambda marker: is_pending_casing_gap(marker, revision),
        "PENDING_UNREPRODUCED: loaded controller/port with unavailable casing footprint",
    )
    pending = session.poll_peek(
        lambda marker: is_pending_casing_gap(marker, revision)
        and marker["game_tick"] >= initial["game_tick"] + 5,
        "PENDING_UNREPRODUCED: missing casing must stay unavailable past onLoad tick",
    )
    session.send(CASING_ADD)
    recovered = session.poll_peek(
        lambda marker: marker["game_tick"] >= pending["game_tick"] + 20
        and _formed_pre_probe(marker, revision),
        "PENDING_UNREPRODUCED: autonomous same-revision formed/visual/binding after 20 game ticks",
    )
    # The first capability query is after both the passive pending and recovery proofs.
    status = session.send("i10probe status", "status")
    if not (
        status is not None and status["validation"] == "VALID"
        and status["runtime"] == "FORMED"
        and status["revision"] == revision
        and status["sentinel"] == "minecraft:diamond"
        and status["count"] == 1
        and status["capability"] is True
        and status["last_known_formed"] is True
    ):
        raise DiagnosticBlocked(f"PENDING_UNREPRODUCED: capability/sentinel mismatch after passive recovery: {status}")
    return {
        "pending_first_observed": initial,
        "unavailable_after_initial_tick": pending,
        "formed_after_retry": recovered,
        "capability_after_recovery": status,
    }


def run_diagnostic(project_root: Path | str, workspace: Path | str | None = None) -> dict[str, object]:
    import run_i10_chunk_acceptance as base

    project = base.validate_project_root(project_root, Path.cwd() if workspace is None else workspace)
    if project.parts[-3:] != (".factory-ci", "i10", "generated"):
        raise DiagnosticBlocked("PENDING: only a disposable .factory-ci/i10/generated fixture is allowed")
    world = project / base.WORLD_RELATIVE
    if world.exists() or world.is_symlink():
        raise DiagnosticBlocked("PENDING: use a fresh fixture; existing world will never be removed")
    output = project / OUTPUT_RELATIVE
    if not base._is_within(output.resolve(strict=False), project):
        raise DiagnosticBlocked("PENDING: diagnostic output must stay inside the project root")
    if output.exists() or output.is_symlink():
        raise DiagnosticBlocked("PENDING: diagnostic output already exists; preserve existing evidence")
    output.mkdir(parents=True)
    base._require_eula(project)
    summary: dict[str, object] = {
        "schema_version": 1,
        "state": "PENDING",
        "scope": "diagnostic_only; negative_control_and_two_client_physical_gate_still_pending",
        "commands": [FULL_ADD, FULL_REMOVE, PARTIAL_ADD, CASING_ADD],
        "phases": [],
    }
    try:
        def prepare(session):
            session.send(FULL_ADD)
            setup = session.send("i10probe setup", "setup")
            if setup is None or not base._formed(setup):
                raise DiagnosticBlocked(f"PENDING: initial formed structure not established: {setup}")
            revision = int(setup["revision"])
            started = session.send("i10probe peek", "peek", "I10_PEEK ")
            if started is None or not _formed_pre_probe(started, revision):
                raise DiagnosticBlocked(f"PENDING: invalid initial visual/binding state: {started}")
            drained = session.poll_peek(
                lambda marker: marker["game_tick"] >= started["game_tick"] + 40
                and _formed_pre_probe(marker, revision),
                "PENDING: drain initial setup ticks before persistence",
            )
            session.send("save-all flush")
            session.send(FULL_REMOVE)
            unloaded = session.poll_peek(
                base._fully_unloaded_pre_probe,
                "PENDING: whole footprint must actually unload before staged restart",
            )
            return revision, {"setup": setup, "drained": drained, "unloaded": unloaded}

        revision, prepared = base._run_phase(project, output, "prepare-full-unload", prepare)
        summary["phases"].append({"phase": "prepare", **prepared})
        observed = _run_diagnostic_phase(
            project, output, "delayed-neighbor-restart",
            lambda session: verify_staged_neighbor_liveness(session, revision),
        )
        summary["phases"].append({"phase": "late_neighbor", **observed})
        summary["state"] = "CONFIRMED"
        return summary
    except (base.AcceptanceError, DiagnosticBlocked) as exc:
        summary["reason"] = str(exc)
        raise
    finally:
        (output / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Fresh disposable .factory-ci/i10/generated project")
    args = parser.parse_args()
    try:
        result = run_diagnostic(args.project)
    except (DiagnosticBlocked, RuntimeError) as exc:
        print(f"I10 DELAYED NEIGHBOR DIAGNOSTIC: PENDING: {exc}")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    print("I10 DELAYED NEIGHBOR DIAGNOSTIC: OBSERVED (review/physical gates remain PENDING)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
