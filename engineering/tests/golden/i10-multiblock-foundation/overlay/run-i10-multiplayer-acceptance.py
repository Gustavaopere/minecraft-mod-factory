#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parent
EVIDENCE_RELATIVE = Path("build/i10-multiplayer-acceptance")
EVIDENCE_ROOT = PROJECT_ROOT / EVIDENCE_RELATIVE
ARCHIVE_ROOT = PROJECT_ROOT / "build/i10-multiplayer-acceptance-archive"
RUN_ROOT = PROJECT_ROOT / "run"
SERVER_RUN = RUN_ROOT / "server"
CLIENT_A_RUN = RUN_ROOT / "clientA"
CLIENT_B_RUN = RUN_ROOT / "clientB"
SERVER_LOG = EVIDENCE_ROOT / "server.log"
CLIENT_A_LOG = EVIDENCE_ROOT / "client-a.log"
CLIENT_B_LOG = EVIDENCE_ROOT / "client-b.log"
METADATA = EVIDENCE_ROOT / "metadata.json"
RAW_ROOT = EVIDENCE_ROOT / "raw"

CLIENT_A_IDENTITY = "I10ClientA"
CLIENT_B_IDENTITY = "I10ClientB"
SERVER_ADDRESS = "127.0.0.1:25565"
WORLD_IDENTITY = "i10-acceptance-world"
TARGET = {
    "minecraft": "1.21.1",
    "neoforge": "21.1.250",
    "java": "21",
}

BASELINE_FORCELoad = "forceload add 159 160 161 160"
BASELINE_SETUP = "i10probe setup"
BASELINE_BREAK = "i10probe break_required_part"
BASELINE_REPAIR = "setblock 159 79 161 i10_multiblock:multiblock_casing"
BASELINE_EXPECTED = (
    "validation=VALID runtime=UNFORMED",
    "capability=false",
    "last_known_formed=false",
)


class AcceptanceError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_metadata(value: dict) -> None:
    METADATA.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_commit(explicit: str | None) -> str:
    if explicit:
        value = explicit.strip().lower()
    else:
        try:
            result = subprocess.run(
                ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise AcceptanceError(
                "cannot resolve exact source commit; rerun with --commit <40-hex-sha>"
            ) from exc
        value = result.stdout.strip().lower()
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise AcceptanceError("acceptance commit must be an exact 40-character hexadecimal SHA")
    return value


def archive_previous_evidence() -> None:
    if not EVIDENCE_ROOT.exists():
        return
    if not any(EVIDENCE_ROOT.iterdir()):
        shutil.rmtree(EVIDENCE_ROOT)
        return
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = ARCHIVE_ROOT / stamp
    counter = 1
    while destination.exists():
        destination = ARCHIVE_ROOT / f"{stamp}-{counter}"
        counter += 1
    shutil.move(str(EVIDENCE_ROOT), str(destination))


def update_properties(path: Path, required: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in required:
            output.append(f"{key}={required[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in required.items():
        if key not in seen:
            output.append(f"{key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def prepare_server_files() -> None:
    SERVER_RUN.mkdir(parents=True, exist_ok=True)
    (SERVER_RUN / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    update_properties(
        SERVER_RUN / "server.properties",
        {
            "online-mode": "false",
            "server-port": "25565",
            "level-name": WORLD_IDENTITY,
            "spawn-protection": "0",
            "allow-flight": "true",
        },
    )


def gradle_command(task: str) -> list[str]:
    if os.name == "nt":
        wrapper = PROJECT_ROOT / "gradlew.bat"
        if not wrapper.is_file():
            raise AcceptanceError(f"missing Gradle wrapper: {wrapper}")
        return [str(wrapper), task, "--no-daemon", "--console=plain"]
    wrapper = PROJECT_ROOT / "gradlew"
    if not wrapper.is_file():
        raise AcceptanceError(f"missing Gradle wrapper: {wrapper}")
    return [str(wrapper), task, "--no-daemon", "--console=plain"]


class LoggedProcess:
    def __init__(
        self,
        name: str,
        command: list[str],
        log_path: Path,
        *,
        stdin_enabled: bool = False,
        echo: bool = False,
    ) -> None:
        self.name = name
        self.command = command
        self.log_path = log_path
        self.stdin_enabled = stdin_enabled
        self.echo = echo
        self.process: subprocess.Popen[str] | None = None
        self.lines: list[str] = []
        self.condition = threading.Condition()
        self.reader: threading.Thread | None = None
        self.launch_count = 0

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            raise AcceptanceError(f"{self.name} is already running")
        if self.reader is not None and self.reader.is_alive():
            self.reader.join(timeout=5)
            if self.reader.is_alive():
                raise AcceptanceError(f"{self.name} previous log reader is still active")

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        kwargs: dict = {
            "cwd": PROJECT_ROOT,
            "stdin": subprocess.PIPE if self.stdin_enabled else subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "bufsize": 1,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        self.process = subprocess.Popen(self.command, **kwargs)
        self.launch_count += 1
        process = self.process
        mode = "w" if self.launch_count == 1 else "a"
        launch_number = self.launch_count
        self.reader = threading.Thread(
            target=self._pump,
            args=(process, mode, launch_number),
            name=f"i10-{self.name}-log-{launch_number}",
            daemon=True,
        )
        self.reader.start()

    def _pump(self, process: subprocess.Popen[str], mode: str, launch_number: int) -> None:
        assert process.stdout is not None
        with self.log_path.open(mode, encoding="utf-8", newline="\n") as output:
            if mode == "a":
                output.write(f"\n===== {self.name} relaunch {launch_number} at {utc_now()} =====\n")
                output.flush()
            for line in process.stdout:
                output.write(line)
                output.flush()
                normalized = line.rstrip("\r\n")
                with self.condition:
                    self.lines.append(normalized)
                    self.condition.notify_all()
                if self.echo:
                    print(f"[{self.name}] {normalized}")
        with self.condition:
            self.condition.notify_all()

    def mark(self) -> int:
        with self.condition:
            return len(self.lines)

    def wait_for(self, predicate: Callable[[str], bool], timeout: float, start: int = 0) -> str:
        deadline = time.monotonic() + timeout
        index = start
        with self.condition:
            while True:
                while index < len(self.lines):
                    line = self.lines[index]
                    index += 1
                    if predicate(line):
                        return line
                if self.process is not None and self.process.poll() is not None:
                    raise AcceptanceError(
                        f"{self.name} exited with code {self.process.returncode} before expected output"
                    )
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise AcceptanceError(f"timed out waiting for {self.name} output")
                self.condition.wait(min(remaining, 1.0))

    def send(self, command: str) -> None:
        if not self.stdin_enabled or self.process is None or self.process.stdin is None:
            raise AcceptanceError(f"{self.name} does not accept console input")
        if self.process.poll() is not None:
            raise AcceptanceError(f"{self.name} is not running")
        print(f"[server-command] {command}")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def terminate_tree(self, timeout: float = 15.0) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        pid = self.process.pid
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                os.killpg(pid, signal.SIGTERM)
            self.process.wait(timeout=timeout)
        except (OSError, subprocess.TimeoutExpired):
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/T", "/F"],
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    os.killpg(pid, signal.SIGKILL)
                self.process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
        if self.reader is not None:
            self.reader.join(timeout=5)


def wait_for_probe(server: LoggedProcess, action: str, timeout: float = 30.0) -> str:
    marker = server.mark()
    server.send(f"i10probe {action}")
    return server.wait_for(
        lambda line: f"I10_PROBE action={action}" in line,
        timeout,
        marker,
    )


def prepare_unformed_baseline(server: LoggedProcess) -> str:
    server.send(BASELINE_FORCELoad)
    wait_for_probe(server, "setup")
    wait_for_probe(server, "break_required_part")
    server.send(BASELINE_REPAIR)
    for _ in range(15):
        marker = server.mark()
        server.send("i10probe status")
        line = server.wait_for(lambda item: "I10_PROBE action=status" in item, 15.0, marker)
        if all(token in line for token in BASELINE_EXPECTED):
            return line
        time.sleep(1.0)
    raise AcceptanceError(
        "baseline did not converge to validation=VALID runtime=UNFORMED capability=false last_known_formed=false"
    )


def copy_tree_if_present(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    elif source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def collect_raw_evidence() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    copy_tree_if_present(SERVER_RUN / "logs", RAW_ROOT / "server-logs")
    copy_tree_if_present(CLIENT_A_RUN / "logs", RAW_ROOT / "client-a-logs")
    copy_tree_if_present(CLIENT_B_RUN / "logs", RAW_ROOT / "client-b-logs")
    copy_tree_if_present(CLIENT_A_RUN / "screenshots", RAW_ROOT / "client-a-screenshots")
    copy_tree_if_present(CLIENT_B_RUN / "screenshots", RAW_ROOT / "client-b-screenshots")
    copy_tree_if_present(SERVER_RUN / "server.properties", RAW_ROOT / "server.properties")


def configure_players(server: LoggedProcess) -> None:
    commands = (
        "time set 1000",
        "difficulty peaceful",
        f"gamemode creative {CLIENT_A_IDENTITY}",
        f"gamemode creative {CLIENT_B_IDENTITY}",
        f"tp {CLIENT_A_IDENTITY} 155.5 80 160.5",
        f"tp {CLIENT_B_IDENTITY} 155.5 80 160.5",
    )
    for command in commands:
        server.send(command)
        time.sleep(0.2)


def reconnect_client_b(
    server: LoggedProcess,
    client_b: LoggedProcess,
    metadata: dict,
    client_join_timeout: int,
) -> None:
    disconnect_marker = server.mark()
    client_b.terminate_tree()
    server.wait_for(
        lambda line: f"{CLIENT_B_IDENTITY} left the game" in line,
        30.0,
        disconnect_marker,
    )

    reconnect_started = utc_now()
    join_marker = server.mark()
    client_b.start()
    server.wait_for(
        lambda line: f"{CLIENT_B_IDENTITY} joined the game" in line,
        client_join_timeout,
        join_marker,
    )
    server.send(f"gamemode creative {CLIENT_B_IDENTITY}")
    server.send(f"tp {CLIENT_B_IDENTITY} 155.5 80 160.5")
    reconnect_completed = utc_now()
    metadata.setdefault("client_b_reconnects", []).append(
        {
            "started_timestamp": reconnect_started,
            "completed_timestamp": reconnect_completed,
        }
    )
    write_metadata(metadata)
    print("Client B reconnect completed and appended to client-b.log")


def interactive_console(
    server: LoggedProcess,
    client_b: LoggedProcess,
    metadata: dict,
    client_join_timeout: int,
) -> None:
    print()
    print("I10 multiplayer session READY")
    print("Both real clients were started with --quickPlayMultiplayer at 127.0.0.1:25565.")
    print("Formation must still be performed physically by Client A in Minecraft.")
    print("Launcher commands: status | break | reconnect-b | server <minecraft command> | help | stop")
    while True:
        try:
            raw = input("i10> ").strip()
        except EOFError:
            return
        if not raw:
            continue
        lowered = raw.lower()
        if lowered in {"stop", "quit", "exit"}:
            return
        if lowered == "status":
            server.send("i10probe status")
            continue
        if lowered == "break":
            server.send("i10probe break_required_part")
            continue
        if lowered == "reconnect-b":
            reconnect_client_b(server, client_b, metadata, client_join_timeout)
            continue
        if lowered == "help":
            print("status = i10probe status")
            print("break = i10probe break_required_part")
            print("reconnect-b = disconnect Client B process, wait for leave, relaunch it, and append its log")
            print("server <command> = forward an arbitrary dedicated-server command")
            print("stop = end the session, preserve logs, and stop all launched processes")
            continue
        if lowered.startswith("server ") and len(raw) > len("server "):
            server.send(raw[len("server "):])
            continue
        print("Unknown launcher command. Use: status | break | reconnect-b | server <command> | help | stop")


def run(commit: str, server_ready_timeout: int, client_join_timeout: int) -> int:
    archive_previous_evidence()
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    prepare_server_files()

    metadata = {
        "schema_version": 1,
        "commit_sha": commit,
        "minecraft": TARGET["minecraft"],
        "neoforge": TARGET["neoforge"],
        "java": TARGET["java"],
        "world_identity": WORLD_IDENTITY,
        "server_address": SERVER_ADDRESS,
        "client_a_identity": CLIENT_A_IDENTITY,
        "client_b_identity": CLIENT_B_IDENTITY,
        "start_timestamp": utc_now(),
        "end_timestamp": None,
        "baseline_probe": None,
        "clients_joined_timestamp": None,
        "client_b_reconnects": [],
        "launcher_state": "STARTING",
    }
    write_metadata(metadata)

    server = LoggedProcess(
        "server",
        gradle_command("runServer"),
        SERVER_LOG,
        stdin_enabled=True,
        echo=True,
    )
    client_a = LoggedProcess("client-a", gradle_command("runClientA"), CLIENT_A_LOG)
    client_b = LoggedProcess("client-b", gradle_command("runClientB"), CLIENT_B_LOG)

    processes = (client_a, client_b, server)
    try:
        server.start()
        server.wait_for(
            lambda line: "Done (" in line and "For help" in line,
            server_ready_timeout,
        )

        baseline = prepare_unformed_baseline(server)
        metadata["baseline_probe"] = baseline
        metadata["launcher_state"] = "BASELINE_READY"
        write_metadata(metadata)

        client_a.start()
        client_b.start()
        server.wait_for(
            lambda line: f"{CLIENT_A_IDENTITY} joined the game" in line,
            client_join_timeout,
        )
        server.wait_for(
            lambda line: f"{CLIENT_B_IDENTITY} joined the game" in line,
            client_join_timeout,
        )
        configure_players(server)
        metadata["clients_joined_timestamp"] = utc_now()
        metadata["launcher_state"] = "READY_FOR_PHYSICAL_ACCEPTANCE"
        write_metadata(metadata)

        interactive_console(server, client_b, metadata, client_join_timeout)
        return 0
    except KeyboardInterrupt:
        print("\nStopping I10 multiplayer session...")
        return 130
    finally:
        metadata["launcher_state"] = "STOPPING"
        write_metadata(metadata)
        if server.process is not None and server.process.poll() is None:
            try:
                server.send("stop")
                server.process.wait(timeout=30)
            except (AcceptanceError, subprocess.TimeoutExpired):
                pass
        for process in processes:
            process.terminate_tree()
        collect_raw_evidence()
        metadata["end_timestamp"] = utc_now()
        metadata["launcher_state"] = "STOPPED"
        write_metadata(metadata)
        print(f"Evidence preserved at: {EVIDENCE_ROOT}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Start the I10 dedicated server plus two distinct real NeoForge clients, "
            "prepare the canonical UNFORMED baseline, and preserve complete logs."
        )
    )
    parser.add_argument("--commit", help="exact 40-character Factory commit SHA; auto-detected from Git when omitted")
    parser.add_argument("--server-ready-timeout", type=int, default=300)
    parser.add_argument("--client-join-timeout", type=int, default=300)
    args = parser.parse_args(argv)
    try:
        commit = resolve_commit(args.commit)
        return run(commit, args.server_ready_timeout, args.client_join_timeout)
    except AcceptanceError as exc:
        print(f"I10 multiplayer launcher failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
