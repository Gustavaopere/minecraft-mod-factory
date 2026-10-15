from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "engineering/tests/experiments/i10_synthetic_retry_control.py"
JAVA = Path("src/main/java/dev/example/i10multiblock")
GOLDEN = ROOT / "engineering/tests/golden/i10-multiblock-foundation/overlay" / JAVA


def load_runner():
    assert RUNNER.is_file(), "I10 RED: synthetic retry control runner is missing"
    spec = importlib.util.spec_from_file_location("i10_synthetic_retry_control", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(workspace, variant):
    target = Path(workspace) / ".factory-ci" / "i10" / variant
    paths = [
        "multiblock/MultiblockPattern.java",
        "multiblock/MultiblockControllerBlockEntity.java",
        "acceptance/I10AcceptanceCommands.java",
    ]
    for rel in paths:
        (target / JAVA / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / JAVA / rel).write_text((GOLDEN / rel).read_text(encoding="utf-8"), encoding="utf-8")
    return target


def peek(tick, runtime="PENDING_REVALIDATION", validation="UNAVAILABLE", revision=3, formed=False):
    return dict(action="peek", game_tick=tick, runtime=runtime, validation=validation,
                revision=revision, last_known_formed=True, controller_visual=formed,
                port_visual=formed, port_bound=True)


class FakeSession:
    def __init__(self, markers):
        self.markers = iter(markers)
        self.commands = []

    def send(self, command, expected_action=None, marker_prefix="I10_PROBE "):
        self.commands.append(command)
        if command == "i10probe status":
            return dict(validation="VALID", runtime="FORMED", revision=3, sentinel="minecraft:diamond",
                        count=1, capability=True, last_known_formed=True)
        return None

    def poll_peek(self, predicate, description):
        for x in self.markers:
            if predicate(x):
                return x
        raise RuntimeError("SYNTHETIC BLOCKED: " + description)


class I10SyntheticRetryControlTests(unittest.TestCase):
    def test_positive_and_negative_instrumentation_never_modify_golden(self):
        module = load_runner()
        original = {p.name: p.read_bytes() for p in [
            GOLDEN / "multiblock/MultiblockPattern.java",
            GOLDEN / "multiblock/MultiblockControllerBlockEntity.java",
            GOLDEN / "acceptance/I10AcceptanceCommands.java"]}
        with tempfile.TemporaryDirectory() as tmp:
            for variant in ("positive", "negative"):
                path = fixture(tmp, variant)
                self.assertEqual(path, module.fixture_path(path, variant, Path(tmp)))
                manifest = module.instrument(path, variant)
                self.assertEqual(variant, manifest["variant"])
                self.assertEqual(variant == "negative", manifest["retry_removed_only_in_negative"])
                pattern = (path / JAVA / "multiblock/MultiblockPattern.java").read_text()
                controller = (path / JAVA / "multiblock/MultiblockControllerBlockEntity.java").read_text()
                commands = (path / JAVA / "acceptance/I10AcceptanceCommands.java").read_text()
                self.assertIn("I10_SYNTHETIC_CASING_GAP", pattern)
                self.assertIn("(worldPos.getZ() >> 4) == 9", pattern)
                self.assertNotIn("if (false)", pattern)
                self.assertIn("release_synthetic_gap", commands)
                self.assertIn("MultiblockPattern.releaseSyntheticCasingGap();", commands)
                self.assertIn("schedulePendingRetry(level);", controller)
                revalidate = controller.split("public MultiblockValidationResult revalidate(", 1)[1]
                if variant == "negative":
                    self.assertNotIn("schedulePendingRetry(level);", revalidate.split("if (validation == MultiblockValidationResult.INVALID)", 1)[0])
                else:
                    self.assertIn("schedulePendingRetry(level);", revalidate)
                with self.assertRaisesRegex(module.SyntheticBlocked, "previously instrumented"):
                    module.instrument(path, variant)
        for p in [GOLDEN / "multiblock/MultiblockPattern.java",
                  GOLDEN / "multiblock/MultiblockControllerBlockEntity.java",
                  GOLDEN / "acceptance/I10AcceptanceCommands.java"]:
            self.assertEqual(original[p.name], p.read_bytes(), "golden source was mutated")

    def test_bad_variant_wrong_workspace_and_changed_source_fail_closed(self):
        module = load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            project = fixture(tmp, "positive")
            with self.assertRaises(module.SyntheticBlocked):
                module.fixture_path(project, "unknown", Path(tmp))
            with self.assertRaises(module.SyntheticBlocked):
                module.fixture_path(project, "negative", Path(tmp))
            path = project / JAVA / "multiblock/MultiblockPattern.java"
            path.write_text(path.read_text().replace(
                "    private MultiblockPattern() {", "    private MultiblockPatternChanged() {"))
            with self.assertRaisesRegex(module.SyntheticBlocked, "unique Java source anchor"):
                module.instrument(project, "positive")

    def test_source_anchoring_is_exact(self):
        module = load_runner()
        self.assertEqual("fixed", module.replace_exact("anchor", "anchor", "fixed"))
        with self.assertRaises(module.SyntheticBlocked):
            module.replace_exact("anchor anchor", "anchor", "wrong")
        with self.assertRaises(module.SyntheticBlocked):
            module.replace_exact("absent", "anchor", "wrong")

    def test_positive_is_real_scheduler_observation_after_synthetic_gap(self):
        module = load_runner()
        session = FakeSession([
            peek(100), peek(106), peek(112, runtime="FORMED", validation="VALID", formed=True),
            peek(122, runtime="FORMED", validation="VALID", formed=True),
        ])
        result = module.evaluate_recovery(session, 3, "positive")
        self.assertEqual(122, result["recovered"]["game_tick"])
        self.assertEqual(["forceload add 159 159 161 161", module.RELEASE_COMMAND,
                          "i10probe status"], session.commands)

    def test_negative_must_stay_pending_without_revalidation_probe(self):
        module = load_runner()
        session = FakeSession([peek(100), peek(106), peek(120), peek(166)])
        result = module.evaluate_recovery(session, 3, "negative")
        self.assertEqual(166, result["negative_control_still_pending"]["game_tick"])
        self.assertNotIn("i10probe status", session.commands)
        self.assertEqual(module.RELEASE_COMMAND, session.commands[-1])

    def test_negative_rejects_spurious_recovery(self):
        module = load_runner()
        session = FakeSession([
            peek(100), peek(106), peek(130, runtime="FORMED", validation="VALID", formed=True)])
        with self.assertRaisesRegex(module.SyntheticBlocked, "unexpectedly recovered"):
            module.evaluate_recovery(session, 3, "negative")

    def test_disposable_runner_wont_overwrite_world_or_output(self):
        module = load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            project = fixture(tmp, "positive")
            (project / "run/server/world").mkdir(parents=True)
            with self.assertRaisesRegex(module.SyntheticBlocked, "fresh fixture"):
                module.run_variant(project, "positive")

    def test_session_ensures_cleanup_on_failure(self):
        module = load_runner()
        with mock.patch.object(module.base.ServerSession, "start"), \
             mock.patch.object(module.base.ServerSession, "stop_gracefully") as stop, \
             mock.patch.object(module.base.ServerSession, "force_cleanup") as clean, \
             mock.patch.object(module.base.ServerSession, "write_log") as log:
            with self.assertRaisesRegex(RuntimeError, "intentional"):
                module.run_session(Path("."), Path("."), "test",
                                   lambda s: (_ for _ in ()).throw(RuntimeError("intentional")))
            stop.assert_called_once()
            clean.assert_called_once()
            log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
