from __future__ import annotations

import io
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
HARNESS = REPO / "engineering/tooling/multiblock-foundation/run_i10_chunk_acceptance.py"
COMMAND = REPO / (
    "engineering/tests/golden/i10-multiblock-foundation/overlay/src/main/java/"
    "dev/example/i10multiblock/acceptance/I10AcceptanceCommands.java"
)
WORKFLOW = REPO / ".github/workflows/factory-engineering-i10-multiblock-foundation.yml"

EXPECTED_COMMANDS = frozenset(
    {
        "forceload add 159 160 161 160",
        "forceload remove 159 160 161 160",
        "i10probe setup",
        "i10probe status",
        "i10probe break_required_part",
        "save-all flush",
        "stop",
    }
)
GOOD_MARKER = (
    "[Server thread/INFO] I10_PROBE action=status validation=UNAVAILABLE "
    "runtime=PENDING_REVALIDATION revision=7 sentinel=minecraft:diamond count=1 "
    "capability=false last_known_formed=true"
)


def marker_line(
    *,
    action: str = "status",
    validation: str = "VALID",
    runtime: str = "FORMED",
    revision: int = 3,
    sentinel: str = "minecraft:diamond",
    count: int = 1,
    capability: bool = True,
    last_known_formed: bool = True,
) -> str:
    return (
        "[Server thread/INFO] I10_PROBE "
        f"action={action} validation={validation} runtime={runtime} revision={revision} "
        f"sentinel={sentinel} count={count} capability={str(capability).lower()} "
        f"last_known_formed={str(last_known_formed).lower()}\n"
    )


def load_harness():
    if not HARNESS.is_file():
        raise AssertionError("I10 RED: real chunk acceptance harness is missing")
    spec = importlib.util.spec_from_file_location("i10_chunk_acceptance_contract", HARNESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeProcess:
    def __init__(self, lines=(), returncode=None):
        self.stdout = iter(lines)
        self.stdin = io.StringIO()
        self.returncode = returncode
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def kill(self):
        self.killed = True
        self.returncode = -9


class I10ChunkAcceptanceContract(unittest.TestCase):
    def test_harness_surface_is_target_exact_and_shell_free(self) -> None:
        module = load_harness()
        text = HARNESS.read_text(encoding="utf-8")
        self.assertEqual((159, 80, 160), module.CONTROLLER_POS)
        self.assertEqual("west", module.CONTROLLER_FACING)
        self.assertEqual('For help, type "help"', module.SERVER_READY_MARKER)
        self.assertNotIn("shell=True", text)
        self.assertNotIn("os.system(", text)
        self.assertNotIn("subprocess.call(", text)
        for token in (
            "subprocess.Popen",
            "stdin=subprocess.PIPE",
            "stdout=subprocess.PIPE",
            "threading.Thread",
            "terminate()",
            "kill()",
            "finally:",
            "build/i10-acceptance",
        ):
            self.assertIn(token, text)

    def test_gradle_argv_is_fixed_allowlist(self) -> None:
        module = load_harness()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper = root / "gradlew"
            wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
            wrapper.chmod(0o755)
            self.assertEqual(["./gradlew", "--no-daemon", "runServer"], module.server_argv(root))
            wrapper.unlink()
            with self.assertRaises(module.AcceptanceError):
                module.server_argv(root)
            wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
            wrapper.chmod(0o644)
            with self.assertRaises(module.AcceptanceError):
                module.server_argv(root)

    def test_server_console_commands_are_closed_allowlist(self) -> None:
        module = load_harness()
        text = HARNESS.read_text(encoding="utf-8")
        self.assertEqual(EXPECTED_COMMANDS, frozenset(module.ALLOWED_SERVER_COMMANDS))
        self.assertIn('session.send("forceload remove 159 160 161 160")', text)
        self.assertNotIn('session.send("forceload remove 161 160")', text)
        self.assertTrue(module.is_allowed_server_command("i10probe status"))
        self.assertFalse(module.is_allowed_server_command("op somebody"))
        self.assertFalse(module.is_allowed_server_command("forceload add 0 0"))

    def test_probe_marker_parser_is_strict_and_typed(self) -> None:
        module = load_harness()
        marker = module.parse_probe_marker(GOOD_MARKER)
        self.assertEqual("status", marker["action"])
        self.assertEqual("UNAVAILABLE", marker["validation"])
        self.assertEqual("PENDING_REVALIDATION", marker["runtime"])
        self.assertEqual(7, marker["revision"])
        self.assertEqual("minecraft:diamond", marker["sentinel"])
        self.assertEqual(1, marker["count"])
        self.assertFalse(marker["capability"])
        self.assertTrue(marker["last_known_formed"])

        bad = (
            "plain server line",
            GOOD_MARKER.replace(" revision=7", ""),
            GOOD_MARKER + " unknown=value",
            GOOD_MARKER.replace("capability=false", "capability=maybe"),
            GOOD_MARKER.replace("runtime=PENDING_REVALIDATION", "runtime=FORMED runtime=UNFORMED"),
            GOOD_MARKER.replace("action=status", "action=unknown"),
            GOOD_MARKER.replace("validation=UNAVAILABLE", "validation=MAYBE"),
            GOOD_MARKER.replace("runtime=PENDING_REVALIDATION", "runtime=MAYBE"),
            GOOD_MARKER.replace("sentinel=minecraft:diamond", "sentinel=BAD"),
            GOOD_MARKER.replace("revision=7", "revision=-1"),
            GOOD_MARKER.replace("count=1", "count=nope"),
            GOOD_MARKER.replace("action=status", "action"),
        )
        for line in bad:
            with self.subTest(line=line):
                with self.assertRaises(module.AcceptanceError):
                    module.parse_probe_marker(line)

    def test_marker_timeout_diagnostic_tail_is_bounded_and_visible(self) -> None:
        module = load_harness()
        lines = [f"line-{index}\n" for index in range(6)]
        tail = module.recent_output_tail(lines, limit=3)
        self.assertEqual("line-3\nline-4\nline-5\n", tail)
        self.assertEqual("", module.recent_output_tail(lines, limit=0))
        self.assertNotIn("line-2", tail)
        text = HARNESS.read_text(encoding="utf-8")
        self.assertIn("recent server output", text)
        self.assertIn("recent_output_tail(self.lines)", text)

    def test_project_and_artifact_paths_remain_contained(self) -> None:
        module = load_harness()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project = workspace / "generated"
            project.mkdir()
            resolved = module.validate_project_root(project, workspace)
            self.assertEqual(project.resolve(), resolved)
            output = module.acceptance_output_root(resolved)
            self.assertTrue(output.is_relative_to(resolved))

            with self.assertRaises(module.AcceptanceError):
                module.validate_project_root(workspace, workspace)
            with self.assertRaises(module.AcceptanceError):
                module.validate_project_root(workspace / "missing", workspace)

            symlink = workspace / "project-link"
            symlink.symlink_to(project, target_is_directory=True)
            with self.assertRaises(module.AcceptanceError):
                module.validate_project_root(symlink, workspace)

            outside = workspace.parent / (workspace.name + "-outside")
            outside.mkdir(exist_ok=True)
            try:
                with self.assertRaises(module.AcceptanceError):
                    module.validate_project_root(outside, workspace)
            finally:
                outside.rmdir()

            output.parent.mkdir(parents=True, exist_ok=True)
            output.symlink_to(project, target_is_directory=True)
            with self.assertRaises(module.AcceptanceError):
                module.acceptance_output_root(resolved)
            output.unlink()

    def test_eula_and_world_helpers_are_bounded(self) -> None:
        module = load_harness()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp).resolve()
            module._require_eula(project)
            self.assertEqual("eula=true\n", (project / module.EULA_RELATIVE).read_text(encoding="utf-8"))

            world = project / module.WORLD_RELATIVE
            world.mkdir(parents=True)
            (world / "marker.txt").write_text("old", encoding="utf-8")
            module._clean_world(project)
            self.assertFalse(world.exists())

            outside = project / "outside-world"
            outside.mkdir()
            world.parent.mkdir(parents=True, exist_ok=True)
            world.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(module.AcceptanceError):
                module._clean_world(project)
            world.unlink()

            eula = project / module.EULA_RELATIVE
            eula.unlink()
            eula.symlink_to(outside / "eula.txt")
            with self.assertRaises(module.AcceptanceError):
                module._require_eula(project)

    def test_server_session_start_send_poll_stop_and_logs_without_real_process(self) -> None:
        module = load_harness()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            wrapper = project / "gradlew"
            wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
            wrapper.chmod(0o755)

            process = FakeProcess([f"boot {module.SERVER_READY_MARKER}\n"])
            session = module.ServerSession(project, "unit")
            with mock.patch.object(module.subprocess, "Popen", return_value=process):
                session.start()
            self.assertIs(session.process, process)
            self.assertIsNone(session._next_line(0))

            session.output_queue.put(marker_line(action="setup"))
            session.output_queue.put(marker_line())
            marker = session.send("i10probe status", "status")
            self.assertEqual("FORMED", marker["runtime"])
            self.assertIn("i10probe status\n", process.stdin.getvalue())

            session.output_queue.put(marker_line(runtime="UNFORMED", capability=False, last_known_formed=False))
            session.output_queue.put(marker_line())
            with mock.patch.object(module.time, "sleep", return_value=None):
                polled = session.poll_status(lambda value: value["runtime"] == "FORMED", "formed")
            self.assertEqual("FORMED", polled["runtime"])

            with self.assertRaises(module.AcceptanceError):
                session.send("op somebody")

            dead = module.ServerSession(project, "dead")
            dead.process = FakeProcess(returncode=1)
            with self.assertRaises(module.AcceptanceError):
                dead.send("i10probe status")

            timeout = module.ServerSession(project, "timeout")
            timeout.process = FakeProcess()
            with mock.patch.object(module, "COMMAND_TIMEOUT_SECONDS", 0):
                with self.assertRaises(module.AcceptanceError):
                    timeout.send("i10probe status", "status")
            with mock.patch.object(module, "POLL_TIMEOUT_SECONDS", 0):
                with self.assertRaises(module.AcceptanceError):
                    timeout.poll_status(lambda _value: True, "never")

            session.stop_gracefully()
            self.assertTrue(session.stopped)
            self.assertEqual(0, process.returncode)

            cleanup = module.ServerSession(project, "cleanup")
            cleanup.process = FakeProcess()
            cleanup.force_cleanup()
            self.assertTrue(cleanup.stopped)
            self.assertTrue(cleanup.process.terminated)

            output = project / "logs"
            session.write_log(output)
            self.assertTrue((output / "unit.log").is_file())

            expired = module.ServerSession(project, "not-ready")
            expired.process = FakeProcess()
            with mock.patch.object(module, "STARTUP_TIMEOUT_SECONDS", 0):
                with self.assertRaises(module.AcceptanceError):
                    expired._wait_ready()

    def test_marker_predicates_are_fail_closed(self) -> None:
        module = load_harness()
        formed = module.parse_probe_marker(marker_line())
        self.assertTrue(module._formed(formed))
        self.assertTrue(module._formed(formed, 3))
        self.assertFalse(module._formed(formed, 4))

        unloaded = module.parse_probe_marker(
            marker_line(
                validation="UNAVAILABLE",
                runtime="UNFORMED",
                revision=0,
                sentinel="empty",
                count=0,
                capability=False,
                last_known_formed=False,
            )
        )
        self.assertTrue(module._fully_unloaded(unloaded))
        unloaded["count"] = 1
        self.assertFalse(module._fully_unloaded(unloaded))

        invalid = module.parse_probe_marker(
            marker_line(
                validation="INVALID",
                runtime="UNFORMED",
                revision=3,
                capability=False,
                last_known_formed=False,
            )
        )
        self.assertTrue(module._unformed_invalid(invalid, 3))
        self.assertFalse(module._unformed_invalid(invalid, 4))

    def test_run_phase_always_cleans_up_and_writes_log(self) -> None:
        module = load_harness()
        calls = []

        class FakeSession:
            def __init__(self, project_root, phase):
                calls.append(("init", phase))

            def start(self):
                calls.append(("start", None))

            def stop_gracefully(self):
                calls.append(("stop", None))

            def force_cleanup(self):
                calls.append(("cleanup", None))

            def write_log(self, output_root):
                calls.append(("log", output_root.name))

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(module, "ServerSession", FakeSession):
            root = Path(tmp)
            result = module._run_phase(root, root / "out", "phase", lambda _session: "ok")
        self.assertEqual("ok", result)
        self.assertEqual(["init", "start", "stop", "cleanup", "log"], [item[0] for item in calls])

    def test_full_acceptance_orchestration_passes_with_deterministic_fake_server(self) -> None:
        module = load_harness()

        class FakeAcceptanceSession:
            def __init__(self, phase):
                self.phase = phase

            def send(self, command, expected_action=None):
                if command == "i10probe setup":
                    return module.parse_probe_marker(marker_line(action="setup"))
                if command == "i10probe break_required_part":
                    return module.parse_probe_marker(
                        marker_line(
                            action="break_required_part",
                            validation="INVALID",
                            runtime="PENDING_REVALIDATION",
                            capability=False,
                        )
                    )
                return None

            def poll_status(self, predicate, description):
                if "physical unload" in description:
                    value = module.parse_probe_marker(
                        marker_line(
                            validation="UNAVAILABLE",
                            runtime="UNFORMED",
                            revision=0,
                            sentinel="empty",
                            count=0,
                            capability=False,
                            last_known_formed=False,
                        )
                    )
                elif "UNFORMED/INVALID" in description:
                    value = module.parse_probe_marker(
                        marker_line(
                            validation="INVALID",
                            runtime="UNFORMED",
                            capability=False,
                            last_known_formed=False,
                        )
                    )
                else:
                    value = module.parse_probe_marker(marker_line())
                if not predicate(value):
                    raise AssertionError(f"predicate rejected deterministic fake marker: {description}: {value}")
                return value

        def fake_run_phase(_project, _output, phase, body):
            return body(FakeAcceptanceSession(phase))

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project = workspace / "generated"
            project.mkdir()
            stale_world = project / module.WORLD_RELATIVE
            stale_world.mkdir(parents=True)
            (stale_world / "stale.txt").write_text("stale", encoding="utf-8")
            with mock.patch.object(module, "_run_phase", side_effect=fake_run_phase):
                summary = module.run_acceptance(project, workspace)
            self.assertEqual("PASS", summary["state"])
            self.assertEqual(3, len(summary["phases"]))
            self.assertFalse(stale_world.exists())
            persisted = project / module.OUTPUT_RELATIVE / "summary.json"
            self.assertTrue(persisted.is_file())
            self.assertIn('"state": "PASS"', persisted.read_text(encoding="utf-8"))

    def test_full_acceptance_persists_blocked_summary_on_failure(self) -> None:
        module = load_harness()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project = workspace / "generated"
            project.mkdir()
            with mock.patch.object(module, "_run_phase", side_effect=module.AcceptanceError("boom")):
                with self.assertRaises(module.AcceptanceError):
                    module.run_acceptance(project, workspace)
            persisted = project / module.OUTPUT_RELATIVE / "summary.json"
            self.assertIn('"state": "BLOCKED"', persisted.read_text(encoding="utf-8"))

    def test_cli_returns_success_and_failure_without_real_server(self) -> None:
        module = load_harness()
        with mock.patch.object(sys, "argv", ["run_i10_chunk_acceptance.py", "--project", "fixture"]), mock.patch.object(
            module, "run_acceptance", return_value={"state": "PASS"}
        ), mock.patch("builtins.print"):
            self.assertEqual(0, module.main())
        with mock.patch.object(sys, "argv", ["run_i10_chunk_acceptance.py", "--project", "fixture"]), mock.patch.object(
            module, "run_acceptance", side_effect=module.AcceptanceError("blocked")
        ), mock.patch("builtins.print"):
            self.assertEqual(1, module.main())

    def test_command_surface_is_fixed_cross_chunk_probe(self) -> None:
        self.assertTrue(COMMAND.is_file(), "I10 RED: I10AcceptanceCommands.java is missing")
        text = COMMAND.read_text(encoding="utf-8")
        for token in (
            "RegisterCommandsEvent",
            'Commands.literal("i10probe")',
            'Commands.literal("setup")',
            'Commands.literal("status")',
            'Commands.literal("break_required_part")',
            "new BlockPos(159, 80, 160)",
            "Direction.WEST",
            "MultiblockPattern.worldPos",
            "Capabilities.ItemHandler.BLOCK",
            "PENDING_REVALIDATION",
            "I10_PROBE",
            "hasPermission(2)",
        ):
            self.assertIn(token, text)

    def test_workflow_runs_real_chunk_acceptance(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Run I10 real chunk acceptance", text)
        self.assertIn(
            "python3 engineering/tooling/multiblock-foundation/run_i10_chunk_acceptance.py --project .factory-ci/i10/generated",
            text,
        )


if __name__ == "__main__":
    unittest.main()
