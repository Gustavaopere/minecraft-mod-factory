from __future__ import annotations

import contextlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PROTOCOL = REPO / "engineering/tests/i10-multiplayer-acceptance.md"
MATERIALIZER = REPO / "engineering/tooling/multiblock-foundation/materialize_i10.py"
PENDING_STATE = "I10_MULTIPLAYER_ACCEPTANCE_STATE=PENDING_MANUAL_MULTIPLAYER_ACCEPTANCE"
PASS_STATE = "I10_MULTIPLAYER_ACCEPTANCE_STATE=PASS"


def load_materializer():
    spec = importlib.util.spec_from_file_location("i10_multiplayer_materializer", MATERIALIZER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_manual_helper(path: Path):
    spec = importlib.util.spec_from_file_location("i10_manual_process", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
            "Manual startup is the default",
            "START-I10-SERVER.bat",
            "START-I10-CLIENT-A.bat",
            "START-I10-CLIENT-B.bat",
            "run-i10-manual-process.py",
            "i10probe baseline",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 multiplayer protocol is incomplete: {missing}")
        self.assertEqual(1, text.count(PENDING_STATE))
        self.assertNotIn(PASS_STATE, text, "I10 multiplayer protocol must not encode PASS before real evidence exists")

    def test_materialized_manual_handoff_runs_one_process_at_a_time_with_complete_logs(self) -> None:
        materializer = load_materializer()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with contextlib.chdir(workspace):
                generated = materializer.materialize_i10("generated")

            helper = generated / "run-i10-manual-process.py"
            self.assertTrue(helper.is_file(), "I10 RED: manual process helper is missing from materialization")
            helper_text = helper.read_text(encoding="utf-8")
            compile(helper_text, str(helper), "exec")
            for token in (
                "runServer",
                "runClientA",
                "runClientB",
                "I10ClientA",
                "I10ClientB",
                "build",
                "i10-multiplayer-acceptance",
                "server.log",
                "client-a.log",
                "client-b.log",
                "metadata.json",
                "raw",
                "GRADLE_USER_HOME",
                ".i10-gradle-user-home",
                "--stacktrace",
                "stdout=subprocess.PIPE",
                "MANUAL_SEPARATE_PROCESSES",
            ):
                self.assertIn(token, helper_text, f"I10 manual helper is incomplete: {token}")
            self.assertNotIn("stdin=subprocess.PIPE", helper_text)

            helper_module = load_manual_helper(helper)
            self.assertEqual("runServer", helper_module.ROLE_CONFIG["server"]["task"])
            self.assertEqual("runClientA", helper_module.ROLE_CONFIG["client-a"]["task"])
            self.assertEqual("runClientB", helper_module.ROLE_CONFIG["client-b"]["task"])
            gradle_env = helper_module.gradle_process_env()
            self.assertEqual(
                str(generated / ".i10-gradle-user-home"),
                gradle_env.get("GRADLE_USER_HOME"),
                "I10 manual physical handoff must isolate NeoGradle from the host-global Gradle cache",
            )
            for task in ("runServer", "runClientA", "runClientB"):
                command = helper_module.gradle_command(task)
                self.assertIn("--stacktrace", command)
                self.assertIn("--no-daemon", command)
                self.assertIn("--console=plain", command)

            manual_files = (
                generated / "START-I10-SERVER.bat",
                generated / "START-I10-CLIENT-A.bat",
                generated / "START-I10-CLIENT-B.bat",
                generated / "START-I10-SERVER.sh",
                generated / "START-I10-CLIENT-A.sh",
                generated / "START-I10-CLIENT-B.sh",
                generated / "PHYSICAL-ACCEPTANCE-README.txt",
            )
            for wrapper in manual_files:
                self.assertTrue(wrapper.is_file(), f"I10 RED: manual physical handoff file is missing: {wrapper.name}")

            self.assertFalse((generated / "START-I10-MULTIPLAYER.bat").exists())
            self.assertFalse((generated / "START-I10-MULTIPLAYER.sh").exists())
            self.assertFalse((generated / "run-i10-multiplayer-acceptance.py").exists())

            server_bat = (generated / "START-I10-SERVER.bat").read_text(encoding="utf-8")
            for token in (
                "I10-SOURCE-COMMIT.txt",
                "run-i10-manual-process.py server",
                "GRADLE_USER_HOME",
                ".i10-gradle-user-home",
            ):
                self.assertIn(token, server_bat, f"I10 Windows server wrapper is missing token: {token}")
            self.assertNotIn("runClientA", server_bat)
            self.assertNotIn("runClientB", server_bat)

            client_a_bat = (generated / "START-I10-CLIENT-A.bat").read_text(encoding="utf-8")
            client_b_bat = (generated / "START-I10-CLIENT-B.bat").read_text(encoding="utf-8")
            self.assertIn("run-i10-manual-process.py client-a", client_a_bat)
            self.assertIn("run-i10-manual-process.py client-b", client_b_bat)
            self.assertIn(".i10-gradle-user-home", client_a_bat)
            self.assertIn(".i10-gradle-user-home", client_b_bat)

            readme_text = (generated / "PHYSICAL-ACCEPTANCE-README.txt").read_text(encoding="utf-8")
            for token in (
                "Manual startup is the default",
                "START-I10-SERVER.bat",
                "START-I10-CLIENT-A.bat",
                "START-I10-CLIENT-B.bat",
                "i10probe baseline",
                "dedicated server",
                "Client A",
                "Client B",
                "Physical formation and visual observations remain required",
            ):
                self.assertIn(token, readme_text, f"I10 physical handoff README is missing token: {token}")

            build_gradle = (generated / "build.gradle").read_text(encoding="utf-8")
            required_gradle_tokens = (
                "clientA",
                "clientB",
                "run 'client'",
                "I10ClientA",
                "I10ClientB",
                "--quickPlayMultiplayer",
                "127.0.0.1:25565",
            )
            missing_gradle = [token for token in required_gradle_tokens if token not in build_gradle]
            self.assertEqual([], missing_gradle, f"I10 multiplayer Gradle runs are incomplete: {missing_gradle}")


if __name__ == "__main__":
    unittest.main()
