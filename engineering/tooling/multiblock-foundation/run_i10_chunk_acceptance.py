#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

CONTROLLER_POS = (159, 80, 160)
CONTROLLER_FACING = "west"
SERVER_READY_MARKER = 'For help, type "help"'
OUTPUT_RELATIVE = Path("build/i10-acceptance")
EULA_RELATIVE = Path("run/server/eula.txt")
WORLD_RELATIVE = Path("run/server/world")
STARTUP_TIMEOUT_SECONDS = 120
POLL_TIMEOUT_SECONDS = 30
COMMAND_TIMEOUT_SECONDS = 15
STOP_TIMEOUT_SECONDS = 20

ALLOWED_SERVER_COMMANDS = frozenset(
    {
        "forceload add 159 160 161 160",
        "forceload remove 159 160 161 160",
        "i10probe baseline",
        "i10probe setup",
        "i10probe status",
        "i10probe break_required_part",
        "save-all flush",
        "stop",
    }
)
EXPECTED_MARKER_KEYS = (
    "action",
    "validation",
    "runtime",
    "revision",
    "sentinel",
    "count",
    "capability",
    "last_known_formed",
)
RESOURCE_ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_/.-]+$")


class AcceptanceError(RuntimeError):
    pass


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def validate_project_root(project_root: Path | str, workspace: Path | str | None = None) -> Path:
    workspace_path = Path.cwd() if workspace is None else Path(workspace)
    workspace_resolved = workspace_path.resolve()
    raw = Path(project_root)
    if raw.is_symlink():
        raise AcceptanceError("I10 acceptance project root must not be a symlink")
    project = raw.resolve()
    if not project.is_dir():
        raise AcceptanceError(f"I10 acceptance project root does not exist: {project}")
    if project == workspace_resolved or not _is_within(project, workspace_resolved):
        raise AcceptanceError("I10 acceptance project must stay inside the workspace and cannot equal its root")
    return project


def acceptance_output_root(project_root: Path) -> Path:
    project = project_root.resolve()
    output = project / OUTPUT_RELATIVE
    if output.is_symlink():
        raise AcceptanceError("I10 acceptance output must not be a symlink")
    resolved = output.resolve(strict=False)
    if resolved == project or not _is_within(resolved, project):
        raise AcceptanceError("I10 acceptance output must stay inside the project root")
    return resolved


def server_argv(project_root: Path) -> list[str]:
    project = project_root.resolve()
    if os.name == "nt":
        wrapper = project / "gradlew.bat"
        if not wrapper.is_file():
            raise AcceptanceError("Gradle wrapper gradlew.bat is required")
        return [str(wrapper), "--no-daemon", "runServer"]
    wrapper = project / "gradlew"
    if not wrapper.is_file():
        raise AcceptanceError("Gradle wrapper ./gradlew is required")
    if not os.access(wrapper, os.X_OK):
        raise AcceptanceError("Gradle wrapper ./gradlew must be executable")
    return ["./gradlew", "--no-daemon", "runServer"]


def is_allowed_server_command(command: str) -> bool:
    return command in ALLOWED_SERVER_COMMANDS


def recent_output_tail(lines: list[str], limit: int = 40) -> str:
    if limit <= 0:
        return ""
    return "".join(lines[-limit:])


def _parse_bool(value: str, key: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise AcceptanceError(f"I10 probe {key} must be true or false")


def _parse_nonnegative_int(value: str, key: str) -> int:
    if not value.isdigit():
        raise AcceptanceError(f"I10 probe {key} must be a non-negative integer")
    return int(value)


def parse_probe_marker(line: str) -> dict[str, object]:
    marker_index = line.find("I10_PROBE ")
    if marker_index < 0:
        raise AcceptanceError("line does not contain an I10_PROBE marker")
    payload = line[marker_index + len("I10_PROBE "):].strip()
    fields: dict[str, str] = {}
    for token in payload.split():
        if token.count("=") != 1:
            raise AcceptanceError(f"malformed I10 probe token: {token!r}")
        key, value = token.split("=", 1)
        if not key or not value:
            raise AcceptanceError(f"malformed I10 probe token: {token!r}")
        if key not in EXPECTED_MARKER_KEYS:
            raise AcceptanceError(f"unknown I10 probe field: {key}")
        if key in fields:
            raise AcceptanceError(f"duplicate I10 probe field: {key}")
        fields[key] = value

    if tuple(fields.keys()) != EXPECTED_MARKER_KEYS:
        missing = [key for key in EXPECTED_MARKER_KEYS if key not in fields]
        raise AcceptanceError(f"I10 probe fields must be exactly ordered; missing={missing}")

    action = fields["action"]
    if action not in {"baseline", "setup", "status", "break_required_part"}:
        raise AcceptanceError(f"invalid I10 probe action: {action}")
    validation = fields["validation"]
    if validation not in {"VALID", "INVALID", "UNAVAILABLE"}:
        raise AcceptanceError(f"invalid I10 probe validation: {validation}")
    runtime = fields["runtime"]
    if runtime not in {"UNFORMED", "PENDING_REVALIDATION", "FORMED"}:
        raise AcceptanceError(f"invalid I10 probe runtime: {runtime}")
    sentinel = fields["sentinel"]
    if sentinel != "empty" and not RESOURCE_ID_RE.fullmatch(sentinel):
        raise AcceptanceError(f"invalid I10 probe sentinel: {sentinel}")

    return {
        "action": action,
        "validation": validation,
        "runtime": runtime,
        "revision": _parse_nonnegative_int(fields["revision"], "revision"),
        "sentinel": sentinel,
        "count": _parse_nonnegative_int(fields["count"], "count"),
        "capability": _parse_bool(fields["capability"], "capability"),
        "last_known_formed": _parse_bool(fields["last_known_formed"], "last_known_formed"),
    }


def _require_eula(project_root: Path) -> None:
    path = project_root / EULA_RELATIVE
    if path.is_symlink():
        raise AcceptanceError("I10 acceptance EULA path must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("eula=true\n", encoding="utf-8")


def _clean_world(project_root: Path) -> None:
    world = project_root / WORLD_RELATIVE
    project = project_root.resolve()
    if world.is_symlink():
        raise AcceptanceError("I10 acceptance world path must not be a symlink")
    resolved = world.resolve(strict=False)
    if not _is_within(resolved, project):
        raise AcceptanceError("I10 acceptance world path escapes project root")
    if world.exists():
        shutil.rmtree(world)


class ServerSession:
    def __init__(self, project_root: Path, phase: str):
        self.project_root = project_root
        self.phase = phase
        self.process: subprocess.Popen[str] | None = None
        self.output_queue: queue.Queue[str | None] = queue.Queue()
        self.reader: threading.Thread | None = None
        self.lines: list[str] = []
        self.stopped = False

    def start(self) -> None:
        self.process = subprocess.Popen(
            server_argv(self.project_root),
            cwd=self.project_root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert self.process.stdout is not None

        def pump_stdout() -> None:
            try:
                for line in self.process.stdout:
                    self.output_queue.put(line)
            finally:
                self.output_queue.put(None)

        self.reader = threading.Thread(
            target=pump_stdout,
            name=f"i10-acceptance-{self.phase}-stdout",
            daemon=True,
        )
        self.reader.start()
        self._wait_ready()

    def _next_line(self, timeout: float) -> str | None:
        try:
            item = self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return ""
        if item is None:
            return None
        self.lines.append(item)
        return item

    def _wait_ready(self) -> None:
        deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            line = self._next_line(0.1)
            if line is None:
                break
            if line and SERVER_READY_MARKER in line:
                return
            if self.process is not None and self.process.poll() is not None and not line:
                break
        raise AcceptanceError(f"{self.phase}: server did not reach ready marker")

    def send(self, command: str, expected_action: str | None = None) -> dict[str, object] | None:
        if not is_allowed_server_command(command):
            raise AcceptanceError(f"{self.phase}: command is not allowlisted: {command!r}")
        if self.process is None or self.process.poll() is not None or self.process.stdin is None:
            raise AcceptanceError(f"{self.phase}: server process is not writable")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        if expected_action is None:
            return None

        deadline = time.monotonic() + COMMAND_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            line = self._next_line(0.1)
            if line is None:
                break
            if not line or "I10_PROBE " not in line:
                continue
            marker = parse_probe_marker(line)
            if marker["action"] == expected_action:
                return marker
        tail = recent_output_tail(self.lines)
        raise AcceptanceError(
            f"{self.phase}: no I10_PROBE action={expected_action} marker observed; "
            f"recent server output:\n{tail}"
        )

    def poll_status(self, predicate, description: str) -> dict[str, object]:
        deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
        last: dict[str, object] | None = None
        while time.monotonic() < deadline:
            marker = self.send("i10probe status", "status")
            assert marker is not None
            last = marker
            if predicate(marker):
                return marker
            time.sleep(0.5)
        raise AcceptanceError(f"{self.phase}: timeout waiting for {description}; last={last}")

    def stop_gracefully(self) -> None:
        if self.process is None or self.process.poll() is not None:
            self.stopped = True
            return
        try:
            self.send("stop")
        except AcceptanceError:
            pass
        try:
            self.process.wait(timeout=STOP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.stopped = True
        if self.reader is not None:
            self.reader.join(timeout=2)
        while True:
            line = self._next_line(0)
            if line in {"", None}:
                break

    def force_cleanup(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        if self.reader is not None:
            self.reader.join(timeout=2)
        self.stopped = True

    def write_log(self, output_root: Path) -> None:
        output_root.mkdir(parents=True, exist_ok=True)
        (output_root / f"{self.phase}.log").write_text("".join(self.lines), encoding="utf-8")


def _baseline_unformed(marker: dict[str, object]) -> bool:
    return (
        marker["validation"] == "VALID"
        and marker["runtime"] == "UNFORMED"
        and marker["revision"] == 0
        and marker["sentinel"] == "empty"
        and marker["count"] == 0
        and marker["capability"] is False
        and marker["last_known_formed"] is False
    )


def _formed(marker: dict[str, object], revision: int | None = None) -> bool:
    return (
        marker["validation"] == "VALID"
        and marker["runtime"] == "FORMED"
        and marker["sentinel"] == "minecraft:diamond"
        and marker["count"] == 1
        and marker["capability"] is True
        and marker["last_known_formed"] is True
        and (revision is None or marker["revision"] == revision)
    )


def _fully_unloaded(marker: dict[str, object]) -> bool:
    return (
        marker["validation"] == "UNAVAILABLE"
        and marker["runtime"] == "UNFORMED"
        and marker["revision"] == 0
        and marker["sentinel"] == "empty"
        and marker["count"] == 0
        and marker["capability"] is False
        and marker["last_known_formed"] is False
    )


def _unformed_invalid(marker: dict[str, object], revision: int) -> bool:
    return (
        marker["validation"] == "INVALID"
        and marker["runtime"] == "UNFORMED"
        and marker["revision"] == revision
        and marker["sentinel"] == "minecraft:diamond"
        and marker["count"] == 1
        and marker["capability"] is False
        and marker["last_known_formed"] is False
    )


def _run_phase(project: Path, output: Path, phase: str, body):
    session = ServerSession(project, phase)
    try:
        session.start()
        return body(session)
    finally:
        try:
            session.stop_gracefully()
        finally:
            session.force_cleanup()
            session.write_log(output)


def run_acceptance(project_root: Path | str, workspace: Path | str | None = None) -> dict[str, object]:
    project = validate_project_root(project_root, Path.cwd() if workspace is None else workspace)
    output = acceptance_output_root(project)
    if output.exists():
        if output.is_symlink():
            raise AcceptanceError("I10 acceptance output must not be a symlink")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    _require_eula(project)
    _clean_world(project)

    summary: dict[str, object] = {
        "schema_version": 1,
        "controller": {"x": CONTROLLER_POS[0], "y": CONTROLLER_POS[1], "z": CONTROLLER_POS[2]},
        "facing": CONTROLLER_FACING,
        "state": "BLOCKED",
        "phases": [],
    }

    try:
        def phase1(session: ServerSession):
            session.send("forceload add 159 160 161 160")
            setup = session.send("i10probe setup", "setup")
            assert setup is not None
            if not _formed(setup):
                raise AcceptanceError(f"phase1: setup did not form exact structure: {setup}")
            revision = int(setup["revision"])
            if revision <= 0:
                raise AcceptanceError(f"phase1: formation revision must be positive: {setup}")

            session.send("save-all flush")
            session.send("forceload remove 159 160 161 160")
            unloaded = session.poll_status(
                _fully_unloaded,
                "physical unload of the complete multiblock footprint",
            )
            session.send("forceload add 159 160 161 160")
            recovered = session.poll_status(
                lambda marker: _formed(marker, revision),
                "FORMED recovery with same revision/sentinel after real footprint reload",
            )
            session.send("save-all flush")
            return revision, {"setup": setup, "unloaded": unloaded, "recovered": recovered}

        revision, phase1_data = _run_phase(project, output, "phase1-unload-reload", phase1)
        summary["phases"].append({"phase": "unload_reload", **phase1_data})

        def phase2(session: ServerSession):
            session.send("forceload add 159 160 161 160")
            recovered = session.poll_status(
                lambda marker: _formed(marker, revision),
                "persisted FORM state after server restart",
            )
            broken = session.send("i10probe break_required_part", "break_required_part")
            assert broken is not None
            if not (
                broken["validation"] == "INVALID"
                and broken["runtime"] == "PENDING_REVALIDATION"
                and broken["revision"] == revision
                and broken["sentinel"] == "minecraft:diamond"
                and broken["count"] == 1
                and broken["capability"] is False
                and broken["last_known_formed"] is True
            ):
                raise AcceptanceError(f"phase2: break mutation did not fail closed pending: {broken}")
            session.send("save-all flush")
            return {"recovered_after_restart": recovered, "broken_before_restart": broken}

        phase2_data = _run_phase(project, output, "phase2-restart-break", phase2)
        summary["phases"].append({"phase": "restart_break", **phase2_data})

        def phase3(session: ServerSession):
            session.send("forceload add 159 160 161 160")
            resolved = session.poll_status(
                lambda marker: _unformed_invalid(marker, revision),
                "UNFORMED/INVALID resolution of stale persisted formed history",
            )
            session.send("save-all flush")
            return {"resolved_after_restart": resolved}

        phase3_data = _run_phase(project, output, "phase3-broken-restart", phase3)
        summary["phases"].append({"phase": "broken_restart", **phase3_data})

        def phase4(session: ServerSession):
            session.send("forceload add 159 160 161 160")
            baseline = session.send("i10probe baseline", "baseline")
            assert baseline is not None
            if not _baseline_unformed(baseline):
                raise AcceptanceError(f"phase4: deterministic manual baseline was not exact: {baseline}")
            stable = session.poll_status(
                _baseline_unformed,
                "stable VALID/UNFORMED manual multiplayer baseline",
            )
            return {"baseline": baseline, "stable": stable}

        phase4_data = _run_phase(project, output, "phase4-manual-baseline", phase4)
        summary["phases"].append({"phase": "manual_baseline", **phase4_data})
        summary["state"] = "PASS"
        return summary
    finally:
        output.mkdir(parents=True, exist_ok=True)
        (output / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run I10 real chunk unload/reload acceptance")
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        summary = run_acceptance(args.project)
    except AcceptanceError as exc:
        print(f"I10 CHUNK ACCEPTANCE: BLOCKED: {exc}")
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("I10 CHUNK ACCEPTANCE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
