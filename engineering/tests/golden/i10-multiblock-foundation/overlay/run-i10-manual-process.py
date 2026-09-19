#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
GRADLE_USER_HOME = PROJECT_ROOT / ".i10-gradle-user-home"
EVIDENCE_ROOT = PROJECT_ROOT / "build" / "i10-multiplayer-acceptance"
ARCHIVE_ROOT = PROJECT_ROOT / "build" / "i10-multiplayer-acceptance-archive"
METADATA_PATH = EVIDENCE_ROOT / "metadata.json"
COMMIT_PATH = PROJECT_ROOT / "I10-SOURCE-COMMIT.txt"

TARGET = {
    "minecraft": "1.21.1",
    "neoforge": "21.1.250",
    "java": "21",
}
WORLD_IDENTITY = "i10-acceptance-world"
CLIENT_A_IDENTITY = "I10ClientA"
CLIENT_B_IDENTITY = "I10ClientB"

ROLE_CONFIG = {
    "server": {
        "task": "runServer",
        "log": EVIDENCE_ROOT / "server.log",
        "run_dir": PROJECT_ROOT / "run" / "server",
    },
    "client-a": {
        "task": "runClientA",
        "log": EVIDENCE_ROOT / "client-a.log",
        "run_dir": PROJECT_ROOT / "run" / "clientA",
    },
    "client-b": {
        "task": "runClientB",
        "log": EVIDENCE_ROOT / "client-b.log",
        "run_dir": PROJECT_ROOT / "run" / "clientB",
    },
}


class ManualHandoffError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_commit() -> str:
    if not COMMIT_PATH.is_file():
        raise ManualHandoffError("I10-SOURCE-COMMIT.txt is missing")
    commit = COMMIT_PATH.read_text(encoding="utf-8").strip()
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ManualHandoffError("I10-SOURCE-COMMIT.txt must contain one full lowercase Git commit SHA")
    return commit


def archive_previous_evidence() -> None:
    if not EVIDENCE_ROOT.exists():
        return
    if EVIDENCE_ROOT.is_symlink():
        raise ManualHandoffError("evidence root must not be a symlink")
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = ARCHIVE_ROOT / stamp
    suffix = 1
    while destination.exists():
        destination = ARCHIVE_ROOT / f"{stamp}-{suffix}"
        suffix += 1
    EVIDENCE_ROOT.replace(destination)


def write_metadata_start(commit: str) -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_ROOT / "screenshots").mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": 1,
        "commit_sha": commit,
        "minecraft": TARGET["minecraft"],
        "neoforge": TARGET["neoforge"],
        "java": TARGET["java"],
        "world_identity": WORLD_IDENTITY,
        "server_address": "127.0.0.1:25565",
        "client_a_identity": CLIENT_A_IDENTITY,
        "client_b_identity": CLIENT_B_IDENTITY,
        "start_timestamp": utc_now(),
        "end_timestamp": None,
        "startup_mode": "MANUAL_SEPARATE_PROCESSES",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_metadata_end() -> None:
    if not METADATA_PATH.is_file():
        return
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    metadata["end_timestamp"] = utc_now()
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_properties(path: Path, replacements: dict[str, str]) -> None:
    existing: dict[str, str] = {}
    order: list[str] = []
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if "=" not in raw or raw.lstrip().startswith("#"):
                continue
            key, value = raw.split("=", 1)
            if key not in existing:
                order.append(key)
            existing[key] = value
    for key, value in replacements.items():
        if key not in existing:
            order.append(key)
        existing[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{key}={existing[key]}\n" for key in order), encoding="utf-8")


def prepare_server_files() -> None:
    server_run = ROLE_CONFIG["server"]["run_dir"]
    assert isinstance(server_run, Path)
    server_run.mkdir(parents=True, exist_ok=True)
    (server_run / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    update_properties(
        server_run / "server.properties",
        {
            "online-mode": "false",
            "server-port": "25565",
            "level-name": WORLD_IDENTITY,
            "spawn-protection": "0",
            "allow-flight": "true",
        },
    )


def gradle_process_env() -> dict[str, str]:
    GRADLE_USER_HOME.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["GRADLE_USER_HOME"] = str(GRADLE_USER_HOME)
    return env


def gradle_command(task: str) -> list[str]:
    if os.name == "nt":
        wrapper = PROJECT_ROOT / "gradlew.bat"
    else:
        wrapper = PROJECT_ROOT / "gradlew"
    if not wrapper.is_file():
        raise ManualHandoffError(f"missing Gradle wrapper: {wrapper}")
    return [str(wrapper), task, "--no-daemon", "--console=plain", "--stacktrace"]


def copy_tree_if_present(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    elif source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def collect_raw(role: str) -> None:
    config = ROLE_CONFIG[role]
    run_dir = config["run_dir"]
    assert isinstance(run_dir, Path)
    raw = EVIDENCE_ROOT / "raw"
    if role == "server":
        copy_tree_if_present(run_dir / "logs", raw / "server-logs")
        copy_tree_if_present(run_dir / "server.properties", raw / "server.properties")
    elif role == "client-a":
        copy_tree_if_present(run_dir / "logs", raw / "client-a-logs")
        copy_tree_if_present(run_dir / "screenshots", raw / "client-a-screenshots")
    else:
        copy_tree_if_present(run_dir / "logs", raw / "client-b-logs")
        copy_tree_if_present(run_dir / "screenshots", raw / "client-b-screenshots")


def run_role(role: str) -> int:
    commit = read_commit()
    if role == "server":
        archive_previous_evidence()
        write_metadata_start(commit)
        prepare_server_files()
    elif not METADATA_PATH.is_file():
        raise ManualHandoffError("start the dedicated server first so metadata.json exists")

    config = ROLE_CONFIG[role]
    task = config["task"]
    log_path = config["log"]
    assert isinstance(task, str)
    assert isinstance(log_path, Path)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    append = role != "server" and log_path.exists()
    mode = "a" if append else "w"

    print(f"I10 source commit: {commit}")
    print(f"Starting {role} with {task}")
    print(f"Evidence log: {log_path}")
    if role == "server":
        print("After the server reports Done, prepare the baseline from this console.")
    elif role == "client-b" and append:
        print("Appending a Client B relaunch to client-b.log for reconnect evidence.")

    command = gradle_command(task)
    process: subprocess.Popen[str] | None = None
    try:
        with log_path.open(mode, encoding="utf-8", newline="\n") as output:
            if append:
                output.write(f"\n===== {role} relaunch at {utc_now()} =====\n")
                output.flush()
            process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                env=gradle_process_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                output.write(line)
                output.flush()
                print(line, end="", flush=True)
            return process.wait()
    finally:
        collect_raw(role)
        if role == "server":
            write_metadata_end()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run exactly one I10 physical-acceptance process and preserve its evidence log."
    )
    parser.add_argument("role", choices=tuple(ROLE_CONFIG))
    args = parser.parse_args(argv)
    try:
        return run_role(args.role)
    except ManualHandoffError as exc:
        print(f"I10 manual handoff failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
