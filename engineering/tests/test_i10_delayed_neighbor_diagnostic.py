from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "engineering/tooling/multiblock-foundation/run_i10_delayed_neighbor_diagnostic.py"


def load_diagnostic():
    assert SCRIPT.is_file(), "I10 RED: delayed-neighbor diagnostic is missing"
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("i10_delayed_neighbor_diagnostic", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def peek(*, tick: int, validation: str = "UNAVAILABLE", runtime: str = "PENDING_REVALIDATION",
         revision: int = 3, last_known_formed: bool = True, controller_visual: bool = False,
         port_visual: bool = False, port_bound: bool = True):
    return dict(validation=validation, runtime=runtime, revision=revision,
                last_known_formed=last_known_formed, controller_visual=controller_visual,
                port_visual=port_visual, port_bound=port_bound, game_tick=tick)


class FakeSession:
    def __init__(self, samples):
        self.samples = iter(samples)
        self.commands = []
        self.observed = []

    def send(self, command, expected_action=None, marker_prefix="I10_PROBE "):
        self.commands.append(command)
        if command == "i10probe status":
            return dict(validation="VALID", runtime="FORMED", revision=3,
                        sentinel="minecraft:diamond", count=1, capability=True,
                        last_known_formed=True)
        return None

    def poll_peek(self, predicate, description):
        for value in self.samples:
            self.observed.append(value)
            if predicate(value):
                return value
        raise RuntimeError("PENDING_UNREPRODUCED: " + description)


class DelayedNeighborDiagnosticTest(unittest.TestCase):
    def test_pending_requires_real_unavailable_chunk_while_port_stays_loaded(self):
        module = load_diagnostic()
        self.assertTrue(module.is_pending_casing_gap(peek(tick=100), 3))
        self.assertFalse(module.is_pending_casing_gap(peek(tick=100, port_bound=False), 3))
        self.assertFalse(module.is_pending_casing_gap(peek(tick=100, validation="VALID"), 3))
        self.assertFalse(module.is_pending_casing_gap(peek(tick=100, runtime="FORMED"), 3))
        self.assertFalse(module.is_pending_casing_gap(peek(tick=100, revision=2), 3))
        self.assertFalse(module.is_pending_casing_gap(peek(tick=100, controller_visual=True), 3))

    def test_probe_requires_quiescent_unavailable_and_waits_for_recovery_before_status(self):
        module = load_diagnostic()
        session = FakeSession([
            peek(tick=100), peek(tick=102), peek(tick=105),
            peek(tick=108, validation="VALID", runtime="FORMED", controller_visual=True,
                 port_visual=True),
            peek(tick=124, validation="VALID", runtime="FORMED", controller_visual=True,
                 port_visual=True),
            peek(tick=125, validation="VALID", runtime="FORMED", controller_visual=True,
                 port_visual=True),
        ])
        evidence = module.verify_staged_neighbor_liveness(session, 3)
        self.assertEqual([module.PARTIAL_ADD, module.CASING_ADD, "i10probe status"], session.commands)
        self.assertEqual(105, evidence["unavailable_after_initial_tick"]["game_tick"])
        self.assertEqual(125, evidence["formed_after_retry"]["game_tick"])
        self.assertEqual(3, evidence["formed_after_retry"]["revision"])

    def test_missing_real_unavailable_marker_is_blocked_before_loading_rest(self):
        module = load_diagnostic()
        session = FakeSession([
            peek(tick=100, validation="VALID", runtime="FORMED",
                 controller_visual=True, port_visual=True),
        ])
        with self.assertRaisesRegex(RuntimeError, "PENDING_UNREPRODUCED"):
            module.verify_staged_neighbor_liveness(session, 3)
        self.assertEqual([module.PARTIAL_ADD], session.commands)



def formed_peek(tick: int, revision: int = 3):
    return peek(tick=tick, validation="VALID", runtime="FORMED", revision=revision,
                controller_visual=True, port_visual=True, port_bound=True)


def formed_status():
    return dict(validation="VALID", runtime="FORMED", revision=3,
                sentinel="minecraft:diamond", count=1, capability=True,
                last_known_formed=True)


class PreparationSession(FakeSession):
    def send(self, command, expected_action=None, marker_prefix="I10_PROBE "):
        if command == "i10probe setup":
            self.commands.append(command)
            return formed_status()
        if command == "i10probe peek":
            self.commands.append(command)
            return formed_peek(10)
        return super().send(command, expected_action, marker_prefix)


class DelayedNeighborExecutionContract(unittest.TestCase):
    def test_diagnostic_commands_remain_isolated_from_canonical_acceptance(self):
        module = load_diagnostic()
        import run_i10_chunk_acceptance as base
        self.assertNotIn(module.PARTIAL_ADD, base.ALLOWED_SERVER_COMMANDS)
        self.assertNotIn(module.CASING_ADD, base.ALLOWED_SERVER_COMMANDS)
        session = module.DiagnosticSession(Path("."), "disposable")
        fake_process = mock.Mock()
        fake_process.poll.return_value = None
        fake_process.stdin = io.StringIO()
        session.process = fake_process
        session.send(module.PARTIAL_ADD)
        session.send(module.CASING_ADD)
        self.assertEqual(module.PARTIAL_ADD + "\n" + module.CASING_ADD + "\n",
                         fake_process.stdin.getvalue())
        with self.assertRaises(module.DiagnosticBlocked):
            session.send(module.PARTIAL_ADD, "not-allowed")
        with self.assertRaises(module.DiagnosticBlocked):
            session.send(module.CASING_ADD, marker_prefix="I10_PEEK ")
        fake_process.poll.return_value = 1
        with self.assertRaises(module.DiagnosticBlocked):
            session.send(module.PARTIAL_ADD)
        fake_process.poll.return_value = None
        with mock.patch.object(module.ServerSession, "send", return_value={"action": "peek"}) as parent:
            self.assertEqual({"action": "peek"}, session.send("i10probe peek", "peek", "I10_PEEK "))
            parent.assert_called_once_with("i10probe peek", "peek", "I10_PEEK ")

    def test_non_default_phase_cleans_up_even_if_body_fails(self):
        module = load_diagnostic()
        with mock.patch.object(module.DiagnosticSession, "start") as start, \
             mock.patch.object(module.DiagnosticSession, "stop_gracefully") as stop, \
             mock.patch.object(module.DiagnosticSession, "force_cleanup") as cleanup, \
             mock.patch.object(module.DiagnosticSession, "write_log") as write_log:
            self.assertEqual(3, module._run_diagnostic_phase(
                Path("."), Path("."), "success", lambda session: 3))
            with self.assertRaisesRegex(RuntimeError, "deliberate failure"):
                module._run_diagnostic_phase(
                    Path("."), Path("."), "failure",
                    lambda session: (_ for _ in ()).throw(RuntimeError("deliberate failure")))
            self.assertEqual(2, start.call_count)
            self.assertEqual(2, stop.call_count)
            self.assertEqual(2, cleanup.call_count)
            self.assertEqual(2, write_log.call_count)

    def test_live_staging_function_rejects_recovery_before_minimum_tick(self):
        module = load_diagnostic()
        session = FakeSession([peek(tick=100), peek(tick=105), formed_peek(124)])
        with self.assertRaisesRegex(RuntimeError, "PENDING_UNREPRODUCED"):
            module.verify_staged_neighbor_liveness(session, 3)
        self.assertEqual([module.PARTIAL_ADD, module.CASING_ADD], session.commands)

    def test_live_staging_function_rejects_invalid_capability_after_passive_recovery(self):
        module = load_diagnostic()
        class WrongSentinel(FakeSession):
            def send(self, command, expected_action=None, marker_prefix="I10_PROBE "):
                result = super().send(command, expected_action, marker_prefix)
                if command == "i10probe status":
                    result["sentinel"] = "empty"
                return result
        session = WrongSentinel([peek(tick=100), peek(tick=105), formed_peek(125)])
        with self.assertRaisesRegex(module.DiagnosticBlocked, "capability/sentinel mismatch"):
            module.verify_staged_neighbor_liveness(session, 3)
        self.assertEqual("i10probe status", session.commands[-1])

    def test_disposable_root_and_prior_world_and_output_are_rejected(self):
        module = load_diagnostic()
        import run_i10_chunk_acceptance as base
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            invalid = workspace / "other"
            invalid.mkdir()
            with self.assertRaisesRegex(module.DiagnosticBlocked, "disposable"):
                module.run_diagnostic(invalid, workspace)
            project = workspace / ".factory-ci" / "i10" / "generated"
            project.mkdir(parents=True)
            world = project / base.WORLD_RELATIVE
            world.mkdir(parents=True)
            with self.assertRaisesRegex(module.DiagnosticBlocked, "existing world"):
                module.run_diagnostic(project, workspace)
            world.rmdir()
            output = project / module.OUTPUT_RELATIVE
            output.mkdir(parents=True)
            with self.assertRaisesRegex(module.DiagnosticBlocked, "already exists"):
                module.run_diagnostic(project, workspace)
            output.rmdir()
            output.parent.rmdir()
            outside = workspace / "outside"
            outside.mkdir()
            (project / "build").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(module.DiagnosticBlocked, "must stay inside"):
                module.run_diagnostic(project, workspace)

    def test_disposable_diagnostic_writes_phase_evidence_and_does_not_claim_physical_pass(self):
        module = load_diagnostic()
        import run_i10_chunk_acceptance as base
        unloaded = peek(tick=60, runtime="UNFORMED", revision=0,
                        last_known_formed=False, port_bound=False)
        prepared = PreparationSession([formed_peek(51), unloaded])
        delayed = FakeSession([peek(tick=100), peek(tick=105), formed_peek(125)])
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project = workspace / ".factory-ci" / "i10" / "generated"
            project.mkdir(parents=True)
            def phase(project_root, output, phase_name, body):
                self.assertEqual("prepare-full-unload", phase_name)
                return body(prepared)
            def delayed_phase(project_root, output, phase_name, body):
                self.assertEqual("delayed-neighbor-restart", phase_name)
                return body(delayed)
            with mock.patch.object(base, "_run_phase", side_effect=phase), \
                 mock.patch.object(module, "_run_diagnostic_phase", side_effect=delayed_phase):
                result = module.run_diagnostic(project, workspace)
            self.assertEqual("CONFIRMED", result["state"])
            self.assertIn("negative_control_and_two_client_physical_gate_still_pending", result["scope"])
            self.assertEqual(["prepare", "late_neighbor"], [x["phase"] for x in result["phases"]])
            self.assertEqual(["i10probe status"], [c for c in delayed.commands if c == "i10probe status"])
            self.assertEqual("save-all flush", prepared.commands[-2])
            self.assertEqual(module.FULL_REMOVE, prepared.commands[-1])
            persisted = json.loads((project / module.OUTPUT_RELATIVE / "summary.json").read_text())
            self.assertEqual("CONFIRMED", persisted["state"])

    def test_diagnostic_failure_writes_pending_reason_without_laundering_pass(self):
        module = load_diagnostic()
        import run_i10_chunk_acceptance as base
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project = workspace / ".factory-ci" / "i10" / "generated"
            project.mkdir(parents=True)
            with mock.patch.object(base, "_run_phase",
                                   side_effect=module.DiagnosticBlocked("no initial formation")):
                with self.assertRaisesRegex(module.DiagnosticBlocked, "no initial formation"):
                    module.run_diagnostic(project, workspace)
            result = json.loads((project / module.OUTPUT_RELATIVE / "summary.json").read_text())
            self.assertEqual("PENDING", result["state"])
            self.assertEqual("no initial formation", result["reason"])

    def test_cli_returns_nonzero_for_blocked_and_labels_success_as_diagnostic(self):
        module = load_diagnostic()
        output = io.StringIO()
        with mock.patch.object(module, "run_diagnostic", side_effect=module.DiagnosticBlocked("no chunk gap")), \
             mock.patch.object(sys, "argv", ["i10-diagnostic", "--project", "example"]), \
             contextlib.redirect_stdout(output):
            self.assertEqual(2, module.main())
        self.assertIn("PENDING: no chunk gap", output.getvalue())
        output = io.StringIO()
        with mock.patch.object(module, "run_diagnostic", return_value={"state": "CONFIRMED"}), \
             mock.patch.object(sys, "argv", ["i10-diagnostic", "--project", "example"]), \
             contextlib.redirect_stdout(output):
            self.assertEqual(0, module.main())
        self.assertIn("review/physical gates remain PENDING", output.getvalue())


if __name__ == "__main__":
    unittest.main()
