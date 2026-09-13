from __future__ import annotations

import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PROTOCOL = REPO / "engineering/tests/i10-multiplayer-acceptance.md"
PENDING_STATE = "I10_MULTIPLAYER_ACCEPTANCE_STATE=PENDING_MANUAL_MULTIPLAYER_ACCEPTANCE"
PASS_STATE = "I10_MULTIPLAYER_ACCEPTANCE_STATE=PASS"


class I10MultiplayerAcceptanceGuard(unittest.TestCase):
    def test_real_two_client_protocol_is_versioned_and_fail_closed(self) -> None:
        self.assertTrue(PROTOCOL.is_file(), "I10 RED: real two-client multiplayer protocol is missing")
        text = PROTOCOL.read_text(encoding="utf-8")

        required = (
            PENDING_STATE,
            "Minecraft 1.21.1",
            "NeoForge 21.1.250",
            "Java 21",
            "two real Minecraft clients",
            "Client A",
            "Client B",
            "both clients observe UNFORMED",
            "Client A forms through normal interaction",
            "both clients observe FORMED",
            "server-authoritatively break one required casing",
            "both clients observe UNFORMED and no port IO",
            "disconnect Client B",
            "reconnect Client B",
            "without historical replay",
            "server log",
            "Client A log",
            "Client B log",
            "screenshots",
            "commit SHA",
            "build/i10-multiplayer-acceptance/",
            "Fake players",
            "server-only tests",
            "GameTests",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 multiplayer protocol is incomplete: {missing}")
        self.assertEqual(1, text.count(PENDING_STATE))
        self.assertNotIn(PASS_STATE, text, "I10 multiplayer protocol must not encode PASS before real evidence exists")


if __name__ == "__main__":
    unittest.main()
