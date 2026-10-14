from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "engineering/tooling/multiblock-foundation/run_i10_delayed_neighbor_diagnostic.py"


def load_diagnostic():
    assert SCRIPT.is_file(), "I10 RED: delayed-neighbor diagnostic is missing"
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


if __name__ == "__main__":
    unittest.main()
