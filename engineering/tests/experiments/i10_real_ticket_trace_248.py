#!/usr/bin/env python3
"""E3: version-pinned read-only I10 chunk ticket trace, never a physical gate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "engineering/tooling/multiblock-foundation"
sys.path.insert(0, str(TOOLS))
import run_i10_chunk_acceptance as base  # noqa: E402

EXACT_TARGET = "21.1.248"
OBS_REL = Path("src/main/java/dev/example/i10multiblock/acceptance/I10TicketTrace.java")
OUT = Path("build/i10-real-ticket-trace")
E1_OUT = Path("build/i10-delayed-neighbor-diagnostic")
FOOTPRINT = {(9, 9), (9, 10), (10, 9), (10, 10)}
TARGET_LINE = "neo_version=" + EXACT_TARGET
MARK_TICKET = re.compile(r"I10_TICKET x=(-?\d+) z=(-?\d+) old=(\d+) new=(\d+) tick=(\d+)")
MARK_TICK = re.compile(
    r"I10_CHUNK_TICK tick=(\d+) c=(true|false) p=(true|false) "
    r"a=(true|false) b=(true|false)")
MARK_PEEK = re.compile(r"I10_PEEK action=peek validation=(VALID|INVALID|UNAVAILABLE) "
                       r"runtime=([A-Z_]+) revision=(\d+)")


class TraceBlocked(RuntimeError):
    pass


# No capability query, chunk request, ticket modification, or synthetic mask.
OBSERVER_JAVA = """package dev.example.i10multiblock.acceptance;

import com.mojang.logging.LogUtils;
import dev.example.i10multiblock.I10MultiblockMod;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.level.ChunkTicketLevelUpdatedEvent;
import net.neoforged.neoforge.event.tick.LevelTickEvent;
import org.slf4j.Logger;

@EventBusSubscriber(modid = I10MultiblockMod.MOD_ID)
public final class I10TicketTrace {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final BlockPos CONTROLLER = new BlockPos(159, 80, 160);
    private static final BlockPos PORT = new BlockPos(161, 80, 160);
    private static final BlockPos CASING_A = new BlockPos(159, 80, 159);
    private static final BlockPos CASING_B = new BlockPos(161, 80, 159);

    private I10TicketTrace() {}

    @SubscribeEvent
    public static void onTicket(ChunkTicketLevelUpdatedEvent event) {
        int x = ChunkPos.getX(event.getChunkPos());
        int z = ChunkPos.getZ(event.getChunkPos());
        if ((x == 9 || x == 10) && (z == 9 || z == 10)) {
            LOGGER.info("I10_TICKET x={} z={} old={} new={} tick={}",
                x, z, event.getOldTicketLevel(), event.getNewTicketLevel(),
                event.getLevel().getGameTime());
        }
    }

    @SubscribeEvent
    public static void onTick(LevelTickEvent.Post event) {
        if (!(event.getLevel() instanceof ServerLevel level)) {
            return;
        }
        boolean c = level.hasChunkAt(CONTROLLER);
        boolean p = level.hasChunkAt(PORT);
        boolean a = level.hasChunkAt(CASING_A);
        boolean b = level.hasChunkAt(CASING_B);
        if (c || p || a || b) {
            LOGGER.info("I10_CHUNK_TICK tick={} c={} p={} a={} b={}",
                level.getGameTime(), c, p, a, b);
        }
    }
}
"""


def project_at(value: Path | str, workspace: Path | None = None) -> Path:
    root = base.validate_project_root(value, Path.cwd() if workspace is None else workspace)
    if root.parts[-3:] != (".factory-ci", "i10", "generated"):
        raise TraceBlocked("E3 BLOCKED: only disposable .factory-ci/i10/generated fixture")
    return root


def replace_exact(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise TraceBlocked("E3 BLOCKED: expected exactly one scaffold profile anchor " + old)
    return text.replace(old, new, 1)


def prepare(project: Path) -> dict:
    java = project / OBS_REL
    output = project / OUT
    if any((project / item).exists() or (project / item).is_symlink()
           for item in (base.WORLD_RELATIVE, OBS_REL, OUT, E1_OUT)):
        raise TraceBlocked("E3 BLOCKED: existing world, observer or evidence; no overwrite")
    targets = {
        "gradle.properties": project / "gradle.properties",
        "gradle.lockfile": project / "gradle.lockfile",
    }
    for path in targets.values():
        if path.is_symlink() or not path.is_file() or not base._is_within(path.resolve(), project):
            raise TraceBlocked("E3 BLOCKED: missing/unsafe scaffold target: " + str(path))
    before = {name: file.read_text(encoding="utf-8") for name, file in targets.items()}
    if "neo_version=21.1.250" not in before["gradle.properties"]:
        raise TraceBlocked("E3 BLOCKED: expected canonical 21.1.250 scaffold")
    if "net.neoforged:neoforge:21.1.250=sdk,testSdk" not in before["gradle.lockfile"]:
        raise TraceBlocked("E3 BLOCKED: expected lockfile pin to 21.1.250")
    # Reuse the Factory's existing explicit, version-aware scaffold conversion.
    sys.path.insert(0, str(ROOT / "engineering/tooling/scaffolder"))
    import scaffold_mod
    profile = {"neoforge": EXACT_TARGET}
    updated = {
        "gradle.properties": scaffold_mod._render_target_exact(
            "gradle.properties.tmpl", before["gradle.properties"], profile),
        "gradle.lockfile": scaffold_mod._render_target_exact(
            "gradle.lockfile.tmpl", before["gradle.lockfile"], profile),
    }
    if TARGET_LINE not in updated["gradle.properties"] or "21.1.250" in updated["gradle.lockfile"]:
        raise TraceBlocked("E3 BLOCKED: profile update did not pin the entire fixture")
    for name, path in targets.items():
        path.write_text(updated[name], encoding="utf-8")
    java.parent.mkdir(parents=True, exist_ok=True)
    java.write_text(OBSERVER_JAVA, encoding="utf-8")
    output.mkdir(parents=True)
    evidence = {
        "schema_version": 1,
        "trial": "E3_EXPLORATORY_REAL_CHUNK_TICKETS",
        "fixture": "Minecraft 1.21.1 / NeoForge " + EXACT_TARGET + " / Java 21",
        "physical_modlist_neoforge": EXACT_TARGET,
        "observer_scope": "DISPOSABLE_GENERATED_FIXTURE_ONLY",
        "observer_only": True,
        "no_capability_query": True,
        "no_force_load_in_listener": True,
        "sha256": {name: {
            "before": hashlib.sha256(before[name].encode()).hexdigest(),
            "after": hashlib.sha256(updated[name].encode()).hexdigest()
        } for name in targets},
        "observer_java_sha256": hashlib.sha256(OBSERVER_JAVA.encode()).hexdigest(),
    }
    (output / "preflight.json").write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n")
    return evidence


def analyze(project: Path, experiment_exit_code: int) -> dict:
    source = project / E1_OUT / "delayed-neighbor-restart.log"
    preparation = project / E1_OUT / "prepare-full-unload.log"
    out = project / OUT
    if not out.is_dir() or not (out / "preflight.json").is_file():
        raise TraceBlocked("E3 BLOCKED: preparatory profile evidence missing")
    if not source.is_file() or not preparation.is_file():
        raise TraceBlocked("E3 BLOCKED: both dedicated-server phase logs required")
    raw = source.read_text(encoding="utf-8")
    tickets = [
        {"chunk": [int(m[1]), int(m[2])], "old": int(m[3]), "new": int(m[4]),
         "tick": int(m[5])}
        for m in MARK_TICKET.finditer(raw)
    ]
    samples = [
        {"tick": int(m[1]), "controller": m[2] == "true", "port": m[3] == "true",
         "casing_a": m[4] == "true", "casing_b": m[5] == "true"}
        for m in MARK_TICK.finditer(raw)
    ]
    peeks = [
        {"validation": m[1], "runtime": m[2], "revision": int(m[3])}
        for m in MARK_PEEK.finditer(raw)
    ]
    incomplete = not tickets or not samples or not peeks
    casing_ticks = [s for s in samples if s["controller"] and s["port"]
                    and not (s["casing_a"] and s["casing_b"])]
    all_ticketed = {
        f"{x},{z}": any(k["chunk"] == [x,z] and k["new"] <= 33 for k in tickets)
        for x,z in sorted(FOOTPRINT)
    }
    verdict = ("TRACE_INCOMPLETE" if incomplete else
               "OBSERVED_REAL_PARTIAL_AVAILABILITY_NEEDS_REVIEW" if casing_ticks else
               "OBSERVED_ALL_ADJACENT_CHUNKS_LOADED")
    result = {
        "schema_version": 1, "result": verdict, "script_exit_code": experiment_exit_code,
        "physical_modlist_neoforge": EXACT_TARGET,
        "ticket_events": tickets, "ticket_event_count": len(tickets),
        "tick_sample_count": len(samples),
        "all_four_chunks_ticketed_at_least_once": all_ticketed,
        "initial_tick_sample": samples[0] if samples else None,
        "final_tick_sample": samples[-1] if samples else None,
        "sampled_loaded_controller_missing_casing": casing_ticks[:12],
        "sampled_missing_count": len(casing_ticks),
        "passive_peek_count": len(peeks),
        "unavailable_peek_count": sum(p["validation"] == "UNAVAILABLE" for p in peeks),
        "physical_chunk_race_proven": bool(casing_ticks) and
                                      any(p["validation"] == "UNAVAILABLE" for p in peeks),
        "retry_negative_control": "NOT_PERFORMED",
        "two_real_clients": "PENDING",
        "p2_review_threads": "OPEN",
    }
    (out / "result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare","analyze"))
    parser.add_argument("--project",required=True)
    parser.add_argument("--exit-code",type=int,default=2)
    args=parser.parse_args()
    try:
        project=project_at(args.project)
        result=prepare(project) if args.action=="prepare" else analyze(project,args.exit_code)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0 if args.action=="prepare" or result["result"]!="TRACE_INCOMPLETE" else 2
    except (TraceBlocked,base.AcceptanceError,ValueError) as exc:
        print("E3 BLOCKED: "+str(exc))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
