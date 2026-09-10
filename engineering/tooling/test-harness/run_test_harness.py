#!/usr/bin/env python3
"""Canonical I5 allowlisted test harness for generated NeoForge mod projects."""

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


TARGET_MINECRAFT = "1.21.1"
TARGET_NEOFORGE = "21.1.248"
TARGET_JAVA = 21
MOD_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
OUTPUT_RELATIVE = Path("build/i5-test-harness")
ARTIFACT_RELATIVE = OUTPUT_RELATIVE / "artifacts"
SERVER_EULA_RELATIVE = Path("run/server/eula.txt")
STANDARD_TIMEOUT_SECONDS = 900
SERVER_STARTUP_TIMEOUT_SECONDS = 120
SERVER_READY_MARKER = 'For help, type "help"'

SUITES = (
    ("unit", "unit", "./gradlew --no-daemon test"),
    ("gametest", "gametest", "./gradlew --no-daemon runGameTestServer"),
    ("dedicated_server", "dedicated_server", "./gradlew --no-daemon runServer"),
)


class HarnessError(RuntimeError):
    """Raised when the harness cannot safely execute the canonical contract."""


def _read_gradle_properties(project_root: Path) -> dict[str, str]:
    path = project_root / "gradle.properties"
    if not path.is_file():
        raise HarnessError("gradle.properties is required")

    properties: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


def _project_identity(project_root: Path) -> tuple[str, dict[str, object]]:
    properties = _read_gradle_properties(project_root)
    required = ("mod_id", "minecraft_version", "neo_version", "java_version")
    missing = [key for key in required if not properties.get(key)]
    if missing:
        raise HarnessError(f"missing required gradle properties: {', '.join(missing)}")

    mod_id = properties["mod_id"]
    if not MOD_ID_RE.fullmatch(mod_id):
        raise HarnessError(f"invalid mod_id: {mod_id!r}")

    try:
        java_version = int(properties["java_version"])
    except ValueError as exc:
        raise HarnessError("java_version must be an integer") from exc

    target = {
        "minecraft": properties["minecraft_version"],
        "loader": "neoforge",
        "neoforge": properties["neo_version"],
        "java": java_version,
    }
    expected = {
        "minecraft": TARGET_MINECRAFT,
        "loader": "neoforge",
        "neoforge": TARGET_NEOFORGE,
        "java": TARGET_JAVA,
    }
    if target != expected:
        raise HarnessError(f"target drift rejected: expected {expected}, got {target}")
    return mod_id, target


def _require_server_eula(project_root: Path) -> None:
    eula_path = project_root / SERVER_EULA_RELATIVE
    if eula_path.is_symlink() or not eula_path.is_file():
        raise HarnessError(
            "dedicated server requires explicit EULA acceptance in run/server/eula.txt (eula=true)"
        )

    project_resolved = project_root.resolve()
    eula_resolved = eula_path.resolve()
    if not eula_resolved.is_relative_to(project_resolved):
        raise HarnessError(
            "dedicated server EULA path must remain inside the project root"
        )

    accepted = False
    for raw_line in eula_resolved.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip().lower() == "eula" and value.strip().lower() == "true":
            accepted = True
            break

    if not accepted:
        raise HarnessError(
            "dedicated server requires explicit EULA acceptance in run/server/eula.txt (eula=true)"
        )


def _validated_output_root(project_root: Path) -> Path:
    output_root = project_root / OUTPUT_RELATIVE
    project_resolved = project_root.resolve()
    output_resolved = output_root.resolve()
    if output_root.is_symlink() or not output_resolved.is_relative_to(project_resolved):
        raise HarnessError("I5 output root must remain inside the project root")
    return output_root


def _gradle_argv(project_root: Path, task: str) -> list[str]:
    if os.name == "nt":
        wrapper = project_root / "gradlew.bat"
        if not wrapper.is_file():
            raise HarnessError("Gradle wrapper gradlew.bat is required")
        return [str(wrapper), "--no-daemon", task]

    wrapper = project_root / "gradlew"
    if not wrapper.is_file():
        raise HarnessError("Gradle wrapper ./gradlew is required")
    if not os.access(wrapper, os.X_OK):
        raise HarnessError("Gradle wrapper ./gradlew must be executable")
    return ["./gradlew", "--no-daemon", task]


def _run_standard(project_root: Path, task: str) -> tuple[str, str]:
    argv = _gradle_argv(project_root, task)
    try:
        result = subprocess.run(
            argv,
            cwd=project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=STANDARD_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return "BLOCKED", output + f"\nI5 harness timeout after {STANDARD_TIMEOUT_SECONDS}s\n"
    return ("PASS" if result.returncode == 0 else "BLOCKED"), result.stdout


def _run_dedicated_server(project_root: Path) -> tuple[str, str]:
    argv = _gradle_argv(project_root, "runServer")
    process = subprocess.Popen(
        argv,
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert process.stdout is not None

    output_queue: queue.Queue[str | None] = queue.Queue()

    def pump_stdout() -> None:
        try:
            for line in process.stdout:
                output_queue.put(line)
        finally:
            output_queue.put(None)

    reader = threading.Thread(target=pump_stdout, name="i5-dedicated-server-log", daemon=True)
    reader.start()

    lines: list[str] = []
    ready = False
    stream_closed = False
    deadline = time.monotonic() + SERVER_STARTUP_TIMEOUT_SECONDS

    while time.monotonic() < deadline and not stream_closed:
        try:
            item = output_queue.get(timeout=0.1)
        except queue.Empty:
            if process.poll() is not None and not reader.is_alive():
                break
            continue
        if item is None:
            stream_closed = True
            break
        lines.append(item)
        if SERVER_READY_MARKER in item:
            ready = True
            break

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    reader.join(timeout=2)
    while True:
        try:
            item = output_queue.get_nowait()
        except queue.Empty:
            break
        if item is not None:
            lines.append(item)

    if not ready and time.monotonic() >= deadline:
        lines.append(f"\nI5 harness startup timeout after {SERVER_STARTUP_TIMEOUT_SECONDS}s\n")
    return ("PASS" if ready else "BLOCKED"), "".join(lines)


def _write_log(project_root: Path, suite_id: str, content: str) -> str:
    relative = ARTIFACT_RELATIVE / "logs" / f"{suite_id}.log"
    destination = project_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return relative.as_posix()


def _collect_tree(project_root: Path, source_relative: Path, destination_relative: Path) -> list[str]:
    source = project_root / source_relative
    if source.is_symlink():
        raise HarnessError(f"report source must not be a symlink: {source_relative.as_posix()}")
    if not source.is_dir():
        return []

    project_resolved = project_root.resolve()
    source_resolved = source.resolve()
    if not source_resolved.is_relative_to(project_resolved):
        raise HarnessError(f"report source escapes project root: {source_relative.as_posix()}")

    collected: list[str] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise HarnessError(
                f"report tree contains symlink: {path.relative_to(source).as_posix()}"
            )
        if not path.is_file():
            continue
        if not path.resolve().is_relative_to(source_resolved):
            raise HarnessError(
                f"report file escapes source root: {path.relative_to(source).as_posix()}"
            )
        relative_inside = path.relative_to(source)
        destination = project_root / destination_relative / relative_inside
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        collected.append(destination.relative_to(project_root).as_posix())
    return collected


def _collect_unit_reports(project_root: Path) -> list[str]:
    evidence: list[str] = []
    evidence.extend(
        _collect_tree(
            project_root,
            Path("build/test-results/test"),
            ARTIFACT_RELATIVE / "test-results/test",
        )
    )
    evidence.extend(
        _collect_tree(
            project_root,
            Path("build/reports/tests/test"),
            ARTIFACT_RELATIVE / "reports/tests/test",
        )
    )
    return evidence


def _write_manifest(project_root: Path, manifest: dict[str, object]) -> Path:
    destination = project_root / OUTPUT_RELATIVE / "test-manifest.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination


def run_harness(project_root):
    """Run the fixed I5 suite allowlist and return the canonical test manifest."""
    project = Path(project_root).expanduser().resolve()
    if not project.is_dir():
        raise HarnessError(f"project root does not exist: {project}")

    mod_id, target = _project_identity(project)
    _require_server_eula(project)
    output_root = _validated_output_root(project)
    if output_root.exists():
        shutil.rmtree(output_root)

    suite_results: list[dict[str, object]] = []
    for suite_id, suite_type, command in SUITES:
        task = command.rsplit(" ", 1)[-1]
        if suite_id == "dedicated_server":
            state, output = _run_dedicated_server(project)
        else:
            state, output = _run_standard(project, task)

        evidence = [_write_log(project, suite_id, output)]
        if suite_id == "unit":
            evidence.extend(_collect_unit_reports(project))

        suite_results.append(
            {
                "suite_id": suite_id,
                "type": suite_type,
                "state": state,
                "command": command,
                "evidence": evidence,
            }
        )

    overall_state = "PASS" if all(suite["state"] == "PASS" for suite in suite_results) else "BLOCKED"
    manifest: dict[str, object] = {
        "schema_version": 1,
        "mod_id": mod_id,
        "target": target,
        "suites": suite_results,
        "overall_state": overall_state,
    }
    _write_manifest(project, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the canonical I5 NeoForge test harness")
    parser.add_argument("--project", required=True, help="Path to the generated mod project")
    args = parser.parse_args()

    try:
        manifest = run_harness(args.project)
    except HarnessError as exc:
        print(f"BLOCKED: {exc}")
        return 2

    print(f"I5 test harness: {manifest['overall_state']}")
    return 0 if manifest["overall_state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
