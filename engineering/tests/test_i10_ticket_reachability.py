"""I10 ticket topology contract; models steady-state vanilla ticket propagation only.

This test does NOT observe live chunk unloads or certify recovery from UNAVAILABLE.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERN = ROOT / ("engineering/tests/golden/i10-multiblock-foundation/overlay/src/main/"
                  "java/dev/example/i10multiblock/multiblock/MultiblockPattern.java")
COMMANDS = ROOT / ("engineering/tests/golden/i10-multiblock-foundation/overlay/src/main/"
                   "java/dev/example/i10multiblock/acceptance/I10AcceptanceCommands.java")
E1 = ROOT / "engineering/tests/i10-delayed-neighbor-live-experiment.md"

FORCED_TICKET_LEVEL = 31
FULL_CHUNK_MAX_LEVEL = 33


def java_int(name: str, source: str) -> int:
    match = re.search(r"\b" + re.escape(name) + r"\s*=\s*(-?\d+)\s*;", source)
    if match is None:
        raise AssertionError("I10 ticket model requires explicit constant: " + name)
    return int(match.group(1))


def fixture_chunks() -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Read canonical golden geometry; cannot request or load any chunk."""
    p = PATTERN.read_text(encoding="utf-8")
    cmd = COMMANDS.read_text(encoding="utf-8")
    for required in (
        "Direction depth = facing.getOpposite();",
        "Direction right = facing.getClockWise();",
        ".relative(right, localX)",
        ".relative(depth, localZ)",
        "if (!level.hasChunkAt(worldPos))",
    ):
        if required not in p:
            raise AssertionError("I10 ticket model transform/availability drift: " + required)
    m = re.search(r"CONTROLLER_POS\s*=\s*new BlockPos\((\d+),\s*(\d+),\s*(\d+)\)", cmd)
    if m is None or "private static final Direction FACING = Direction.WEST;" not in cmd:
        raise AssertionError("I10 ticket model requires original west-facing acceptance fixture")
    cx, _, cz = map(int, m.groups())
    xs = range(java_int("MIN_X", p), java_int("MAX_X", p) + 1)
    zs = range(java_int("MIN_Z", p), java_int("MAX_Z", p) + 1)
    # WEST: clockwise right = NORTH (-Z), opposite depth = EAST (+X).
    footprint = {((cx + z) // 16, (cz - x) // 16) for x in xs for z in zs}
    forced = {(x // 16, 160 // 16) for x in (159, 161)}
    return footprint, forced


def effective_ticket_level(target: tuple[int, int], sources: set[tuple[int, int]]) -> int:
    if not sources:
        raise ValueError("at least one anchor is required")
    return FORCED_TICKET_LEVEL + min(
        max(abs(target[0] - anchor[0]), abs(target[1] - anchor[1]))
        for anchor in sources
    )


class I10ForceloadTicketTopologyContract(unittest.TestCase):
    def test_canonical_footprint_is_four_adjacent_chunks(self) -> None:
        footprint, forced = fixture_chunks()
        self.assertEqual({(9, 9), (9, 10), (10, 9), (10, 10)}, footprint)
        self.assertEqual({(9, 10), (10, 10)}, forced)
        self.assertTrue(forced.issubset(footprint))

    def test_steady_controller_port_forceload_also_loads_casing_chunks(self) -> None:
        footprint, forced = fixture_chunks()
        levels = {chunk: effective_ticket_level(chunk, forced) for chunk in footprint}
        self.assertEqual({(9, 9): 32, (9, 10): 31, (10, 9): 32, (10, 10): 31}, levels)
        self.assertTrue(all(level <= FULL_CHUNK_MAX_LEVEL for level in levels.values()),
                        "Adjacent casing is accessible in the steady-state ticket model")

    def test_farther_chunks_are_not_automatically_accessible(self) -> None:
        _, forced = fixture_chunks()
        self.assertEqual(33, effective_ticket_level((9, 8), forced))
        self.assertEqual(34, effective_ticket_level((9, 7), forced))
        self.assertGreater(effective_ticket_level((9, 7), forced), FULL_CHUNK_MAX_LEVEL)
        with self.assertRaises(ValueError):
            effective_ticket_level((9, 9), set())

    def test_e1_verdict_is_explicitly_non_acceptance(self) -> None:
        evidence = E1.read_text(encoding="utf-8")
        self.assertIn("PENDING_UNREPRODUCED", evidence)
        self.assertIn("H2 was **not tested**", evidence)
        self.assertIn("retry-disabled negative control", evidence)


if __name__ == "__main__":
    unittest.main()
