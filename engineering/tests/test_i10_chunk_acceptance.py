from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


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
        "forceload remove 161 160",
        "forceload add 161 160",
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


def load_harness():
    if not HARNESS.is_file():
        raise AssertionError("I10 RED: real chunk acceptance harness is missing")
    spec = importlib.util.spec_from_file_location("i10_chunk_acceptance_contract", HARNESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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

    def test_server_console_commands_are_closed_allowlist(self) -> None:
        module = load_harness()
        self.assertEqual(EXPECTED_COMMANDS, frozenset(module.ALLOWED_SERVER_COMMANDS))
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
            GOOD_MARKER.replace(" revision=7", ""),
            GOOD_MARKER + " unknown=value",
            GOOD_MARKER.replace("capability=false", "capability=maybe"),
            GOOD_MARKER.replace("runtime=PENDING_REVALIDATION", "runtime=FORMED runtime=UNFORMED"),
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

            outside = workspace.parent / (workspace.name + "-outside")
            outside.mkdir(exist_ok=True)
            try:
                with self.assertRaises(module.AcceptanceError):
                    module.validate_project_root(outside, workspace)
            finally:
                outside.rmdir()

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
