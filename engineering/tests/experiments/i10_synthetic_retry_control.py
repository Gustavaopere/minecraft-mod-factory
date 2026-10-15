#!/usr/bin/env python3
"""Disposable synthetic-UNAVAILABLE I10 liveness and retry-disabled control.

Never modifies the golden source. Never counts as real missing-chunk proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

TOOLING = Path(__file__).resolve().parents[2] / "tooling/multiblock-foundation"
sys.path.insert(0, str(TOOLING))
import run_i10_chunk_acceptance as base  # noqa: E402

JAVA = Path("src/main/java/dev/example/i10multiblock")
MASK_ENV = "I10_SYNTHETIC_CASING_GAP"
RELEASE_COMMAND = "i10probe release_synthetic_gap"
OUTPUT = Path("build/i10-synthetic-retry-control")


class SyntheticBlocked(RuntimeError):
    pass


def replace_exact(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SyntheticBlocked(f"SYNTHETIC BLOCKED: expected unique Java source anchor: {old!r}")
    return text.replace(old, new, 1)


def fixture_path(project: Path | str, variant: str, workspace: Path | None = None) -> Path:
    if variant not in {"positive", "negative"}:
        raise SyntheticBlocked("SYNTHETIC BLOCKED: variant must be positive or negative")
    path = base.validate_project_root(project, Path.cwd() if workspace is None else workspace)
    if path.parts[-3:] != (".factory-ci", "i10", variant):
        raise SyntheticBlocked("SYNTHETIC BLOCKED: only .factory-ci/i10/{positive,negative} is allowed")
    return path


def instrument(project: Path, variant: str) -> dict[str, object]:
    """Patch copies in a materialized disposable project, never Factory golden source."""
    sources = {
        "pattern": project / JAVA / "multiblock/MultiblockPattern.java",
        "commands": project / JAVA / "acceptance/I10AcceptanceCommands.java",
        "controller": project / JAVA / "multiblock/MultiblockControllerBlockEntity.java",
    }
    before = {}
    for name, path in sources.items():
        if path.is_symlink() or not path.is_file() or not base._is_within(path.resolve(), project):
            raise SyntheticBlocked(f"SYNTHETIC BLOCKED: invalid fixture source: {name}")
        before[name] = path.read_text(encoding="utf-8")
        if "i10SyntheticCasingGap" in before[name] or RELEASE_COMMAND in before[name]:
            raise SyntheticBlocked("SYNTHETIC BLOCKED: fixture appears previously instrumented")

    pattern = replace_exact(before["pattern"],
        "    private MultiblockPattern() {\n",
        '    // Synthetic visibility only; disposable fixture, NEVER the golden runtime.\n'
        '    private static volatile boolean i10SyntheticCasingGap =\n'
        '            "true".equals(System.getenv("I10_SYNTHETIC_CASING_GAP"));\n'
        '    public static void releaseSyntheticCasingGap() {\n'
        '        i10SyntheticCasingGap = false;\n'
        '    }\n\n'
        "    private MultiblockPattern() {\n")
    pattern = replace_exact(pattern,
        "                    if (!level.hasChunkAt(worldPos)) {\n",
        "                    if (!level.hasChunkAt(worldPos)) {\n"
        "                        return MultiblockValidationResult.UNAVAILABLE;\n"
        "                    }\n"
        "                    // The casing chunk is physically loaded; simulate visibility loss.\n"
        "                    if (i10SyntheticCasingGap\n"
        "                            && (worldPos.getX() >> 4) == 9\n"
        "                            && (worldPos.getZ() >> 4) == 9) {\n"
        "                        return MultiblockValidationResult.UNAVAILABLE;\n"
        "                    }\n"
        "                    if (false) {\n")
    # Restore the generated dead-branch placeholder without leaving it in source.
    pattern = replace_exact(pattern, "                    if (false) {\n"
                              "                        return MultiblockValidationResult.UNAVAILABLE;\n"
                              "                    }\n", "")

    commands = replace_exact(before["commands"],
        '                        .then(Commands.literal("break_required_part")\n',
        '                        .then(Commands.literal("release_synthetic_gap")\n'
        '                                .executes(context -> releaseSyntheticGap(context.getSource())))\n'
        '                        .then(Commands.literal("break_required_part")\n')
    commands = replace_exact(commands,
        "    private static int breakRequiredPart(CommandSourceStack source) {\n",
        "    private static int releaseSyntheticGap(CommandSourceStack source) {\n"
        "        MultiblockPattern.releaseSyntheticCasingGap();\n"
        '        LOGGER.info("I10_SYNTHETIC_GAP action=release game_tick={}", source.getLevel().getGameTime());\n'
        "        return 1;\n"
        "    }\n\n"
        "    private static int breakRequiredPart(CommandSourceStack source) {\n")

    controller = before["controller"]
    if variant == "negative":
        signature = "    public MultiblockValidationResult revalidate(ServerLevel level, Direction facing) {\n"
        if controller.count(signature) != 1:
            raise SyntheticBlocked("SYNTHETIC BLOCKED: revalidate entrypoint changed")
        left, right = controller.split(signature, 1)
        right = replace_exact(right,
            "            schedulePendingRetry(level);\n            return validation;\n",
            "            // E2 NEGATIVE CONTROL ONLY: omit the 20-tick retry.\n"
            "            return validation;\n")
        controller = left + signature + right

    changed = {"pattern": pattern, "commands": commands, "controller": controller}
    for name, path in sources.items():
        path.write_text(changed[name], encoding="utf-8")
    return {
        "variant": variant,
        "kind": "SYNTHETIC_UNAVAILABLE_NOT_A_REAL_CHUNK_UNLOAD",
        "input_sha256": {name: hashlib.sha256(s.encode()).hexdigest() for name, s in before.items()},
        "instrumented_sha256": {name: hashlib.sha256(s.encode()).hexdigest() for name, s in changed.items()},
        "retry_removed_only_in_negative": variant == "negative",
    }


class SyntheticSession(base.ServerSession):
    def send(self, command: str, expected_action: str | None = None,
             marker_prefix: str = "I10_PROBE "):
        if command != RELEASE_COMMAND:
            return super().send(command, expected_action, marker_prefix)
        if expected_action is not None or marker_prefix != "I10_PROBE ":
            raise SyntheticBlocked("SYNTHETIC BLOCKED: release cannot request probe markers")
        if self.process is None or self.process.poll() is not None or self.process.stdin is None:
            raise SyntheticBlocked("SYNTHETIC BLOCKED: server not writable")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        return None


def run_session(project: Path, output: Path, name: str, body, session_type=base.ServerSession):
    session = session_type(project, name)
    try:
        session.start()
        return body(session)
    finally:
        try:
            session.stop_gracefully()
        finally:
            session.force_cleanup()
            session.write_log(output)


def pending_marker(marker: dict[str, object], revision: int) -> bool:
    return (
        marker["validation"] == "UNAVAILABLE"
        and marker["runtime"] == "PENDING_REVALIDATION"
        and marker["revision"] == revision
        and marker["last_known_formed"] is True
        and marker["controller_visual"] is False
        and marker["port_visual"] is False
        and marker["port_bound"] is True
    )


def recovered_marker(marker: dict[str, object], revision: int) -> bool:
    return (
        marker["validation"] == "VALID"
        and marker["runtime"] == "FORMED"
        and marker["revision"] == revision
        and marker["last_known_formed"] is True
        and marker["controller_visual"] is True
        and marker["port_visual"] is True
        and marker["port_bound"] is True
    )


def evaluate_recovery(session, revision: int, variant: str) -> dict[str, object]:
    session.send("forceload add 159 159 161 161")
    pending = session.poll_peek(lambda m: pending_marker(m, revision),
                                "SYNTHETIC BLOCKED: actual scheduler did not enter pending")
    sustained = session.poll_peek(
        lambda m: pending_marker(m, revision) and m["game_tick"] >= pending["game_tick"] + 5,
        "SYNTHETIC BLOCKED: unavailable state did not persist beyond onLoad tick")
    session.send(RELEASE_COMMAND)
    if variant == "positive":
        recovered = session.poll_peek(
            lambda m: recovered_marker(m, revision)
            and m["game_tick"] >= pending["game_tick"] + 20,
            "SYNTHETIC BLOCKED: no autonomous recovery after releasing artificial gap")
        verified = session.send("i10probe status", "status")
        if verified is None or not base._formed(verified, revision):
            raise SyntheticBlocked(f"SYNTHETIC BLOCKED: capability/sentinel mismatch: {verified}")
        return {"pending": pending, "sustained": sustained, "recovered": recovered,
                "status_after_recovery": verified}

    def must_remain_pending(marker):
        if recovered_marker(marker, revision):
            raise SyntheticBlocked("SYNTHETIC BLOCKED: negative control unexpectedly recovered")
        if marker["game_tick"] >= sustained["game_tick"] + 60:
            if marker["runtime"] != "PENDING_REVALIDATION" or marker["revision"] != revision:
                raise SyntheticBlocked(f"SYNTHETIC BLOCKED: negative control state changed: {marker}")
            return True
        return False
    remained = session.poll_peek(must_remain_pending,
                                "SYNTHETIC BLOCKED: negative control did not remain pending")
    return {"pending": pending, "sustained": sustained, "negative_control_still_pending": remained}


def run_variant(project: Path, variant: str) -> dict[str, object]:
    world = project / base.WORLD_RELATIVE
    output = project / OUTPUT
    if world.exists() or world.is_symlink() or output.exists() or output.is_symlink():
        raise SyntheticBlocked("SYNTHETIC BLOCKED: fresh fixture required; no world/evidence overwrite")
    if not base._is_within(output.resolve(strict=False), project):
        raise SyntheticBlocked("SYNTHETIC BLOCKED: output path escapes fixture")
    base._require_eula(project)
    output.mkdir(parents=True)
    summary = {"schema_version": 1, "variant": variant, "scope": "SYNTHETIC_UNAVAILABLE_ONLY",
               "state": "BLOCKED", "negative_control_checked": variant == "negative"}
    try:
        def prepare(session):
            session.send("forceload add 159 159 161 161")
            formed = session.send("i10probe setup", "setup")
            if formed is None or not base._formed(formed):
                raise SyntheticBlocked(f"SYNTHETIC BLOCKED: initial formed baseline: {formed}")
            rev = int(formed["revision"])
            start = session.send("i10probe peek", "peek", "I10_PEEK ")
            if start is None or not recovered_marker(start, rev):
                raise SyntheticBlocked("SYNTHETIC BLOCKED: initial visuals not formed")
            drained = session.poll_peek(
                lambda m: m["game_tick"] >= start["game_tick"] + 40 and recovered_marker(m, rev),
                "SYNTHETIC BLOCKED: 40-tick quiescent baseline missing")
            session.send("save-all flush")
            session.send("forceload remove 159 159 161 161")
            unloaded = session.poll_peek(
                base._fully_unloaded_pre_probe,
                "SYNTHETIC BLOCKED: real full-four-chunk unload missing")
            return rev, {"formed": formed, "drained": drained, "unloaded": unloaded}
        revision, first = run_session(project, output, "prepare", prepare)
        summary["prepare"] = first
        before = os.environ.get(MASK_ENV)
        os.environ[MASK_ENV] = "true"
        try:
            result = run_session(project, output, "masked-" + variant,
                                 lambda s: evaluate_recovery(s, revision, variant), SyntheticSession)
        finally:
            if before is None:
                os.environ.pop(MASK_ENV, None)
            else:
                os.environ[MASK_ENV] = before
        summary["observation"] = result
        summary["state"] = "OBSERVED_SYNTHETIC_POSITIVE" if variant == "positive" else "OBSERVED_SYNTHETIC_NEGATIVE"
        return summary
    except (SyntheticBlocked, base.AcceptanceError) as exc:
        summary["reason"] = str(exc)
        raise
    finally:
        (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                              encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("instrument", "run"))
    parser.add_argument("--variant", choices=("positive", "negative"), required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        project = fixture_path(args.project, args.variant)
        result = instrument(project, args.variant) if args.action == "instrument" else run_variant(project, args.variant)
        print(json.dumps(result, sort_keys=True))
    except (SyntheticBlocked, base.AcceptanceError) as exc:
        print(f"I10 SYNTHETIC CONTROL BLOCKED: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
