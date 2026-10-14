#!/usr/bin/env python3
"""E4: observe real onLoad/chunk event ordering before first tick, version-matched.

No test-only availability mask, validator modification, ticket mutation, capability probe,
or change to the canonical golden. Only generated .factory-ci/i10/generated Java changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i10_real_ticket_trace_248 as e3

LOG_REL = Path("build/i10-e4-onload-trace")
CONTROLLER = Path("src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlockEntity.java")
LOAD_RE = re.compile(r"I10_E4_CHUNK phase=(load|unload) x=(-?\d+) z=(-?\d+) nano=(\d+)")
ONLOAD_RE = re.compile(
    r"I10_E4_ONLOAD tick=(\d+) revision=(\d+) c=(true|false) p=(true|false) "
    r"a=(true|false) b=(true|false) nano=(\d+)")
REVALIDATE_RE = re.compile(
    r"I10_E4_REVALIDATE tick=(\d+) revision=(\d+) validation=(VALID|INVALID|UNAVAILABLE) "
    r"c=(true|false) p=(true|false) a=(true|false) b=(true|false) nano=(\d+)")


def anchored(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise e3.TraceBlocked(f"E4 BLOCKED: source anchor drift for {old!r}")
    return source.replace(old, new, 1)


def prepare(project: Path) -> dict:
    output = project / LOG_REL
    if output.exists() or output.is_symlink():
        raise e3.TraceBlocked("E4 BLOCKED: preserve previous evidence, fresh fixture required")
    evidence = e3.prepare(project)
    observer = project / e3.OBS_REL
    controller = project / CONTROLLER
    if controller.is_symlink() or not controller.is_file() or not e3.base._is_within(controller.resolve(),project):
        raise e3.TraceBlocked("E4 BLOCKED: unsafe generated controller")
    pre = {"observer": observer.read_text(encoding="utf-8"),
           "controller": controller.read_text(encoding="utf-8")}
    # ChunkEvent.Load can be fired before FULL: strictly no level access in event handlers.
    updated_observer = anchored(
        pre["observer"],
        "import net.neoforged.neoforge.event.level.ChunkTicketLevelUpdatedEvent;",
        "import net.neoforged.neoforge.event.level.ChunkTicketLevelUpdatedEvent;\n"
        "import net.neoforged.neoforge.event.level.ChunkEvent;")
    updated_observer = anchored(
        updated_observer,
        "    @SubscribeEvent\n    public static void onTicket(ChunkTicketLevelUpdatedEvent event) {",
        '    // No getLevel(), hasChunkAt(), getBlockState(), or chunk promotion here.\n'
        '    @SubscribeEvent\n'
        '    public static void onLoad(ChunkEvent.Load event) {\n'
        '        var pos = event.getChunk().getPos();\n'
        '        if ((pos.x == 9 || pos.x == 10) && (pos.z == 9 || pos.z == 10)) {\n'
        '            LOGGER.info("I10_E4_CHUNK phase=load x={} z={} nano={}",\n'
        '                pos.x, pos.z, System.nanoTime());\n'
        '        }\n'
        '    }\n\n'
        '    @SubscribeEvent\n'
        '    public static void onUnload(ChunkEvent.Unload event) {\n'
        '        var pos = event.getChunk().getPos();\n'
        '        if ((pos.x == 9 || pos.x == 10) && (pos.z == 9 || pos.z == 10)) {\n'
        '            LOGGER.info("I10_E4_CHUNK phase=unload x={} z={} nano={}",\n'
        '                pos.x, pos.z, System.nanoTime());\n'
        '        }\n'
        '    }\n\n'
        '    @SubscribeEvent\n'
        '    public static void onTicket(ChunkTicketLevelUpdatedEvent event) {')

    updated_controller = anchored(
        pre["controller"],
        "        super.onLoad();\n        if (level instanceof ServerLevel serverLevel && lastKnownFormed) {",
        '        super.onLoad();\n'
        '        // Passive snapshot; records readiness at controller onLoad, before scheduled retry.\n'
        '        if (level instanceof ServerLevel e4Level && lastKnownFormed) {\n'
        '            com.mojang.logging.LogUtils.getLogger().info(\n'
        '                "I10_E4_ONLOAD tick={} revision={} c={} p={} a={} b={} nano={}",\n'
        '                e4Level.getGameTime(), formationRevision,\n'
        '                e4Level.hasChunkAt(worldPosition),\n'
        '                e4Level.hasChunkAt(new BlockPos(161, 80, 160)),\n'
        '                e4Level.hasChunkAt(new BlockPos(159, 80, 159)),\n'
        '                e4Level.hasChunkAt(new BlockPos(161, 80, 159)),\n'
        '                System.nanoTime());\n'
        '        }\n'
        '        if (level instanceof ServerLevel serverLevel && lastKnownFormed) {')
    updated_controller = anchored(
        updated_controller,
        "    public MultiblockValidationResult revalidate(ServerLevel level, Direction facing) {\n"
        "        MultiblockValidationResult validation = MultiblockPattern.validate(level, worldPosition, facing);",
        "    public MultiblockValidationResult revalidate(ServerLevel level, Direction facing) {\n"
        "        MultiblockValidationResult validation = MultiblockPattern.validate(level, worldPosition, facing);\n"
        '        com.mojang.logging.LogUtils.getLogger().info(\n'
        '            "I10_E4_REVALIDATE tick={} revision={} validation={} c={} p={} a={} b={} nano={}",\n'
        '            level.getGameTime(), formationRevision, validation.name(),\n'
        '            level.hasChunkAt(worldPosition),\n'
        '            level.hasChunkAt(new BlockPos(161, 80, 160)),\n'
        '            level.hasChunkAt(new BlockPos(159, 80, 159)),\n'
        '            level.hasChunkAt(new BlockPos(161, 80, 159)),\n'
        '            System.nanoTime());')
    updated = {"observer": updated_observer, "controller": updated_controller}
    for name, file in [("observer", observer), ("controller", controller)]:
        file.write_text(updated[name], encoding="utf-8")
    output.mkdir(parents=True)
    report = {
        "schema_version": 1, "trial": "E4_EXPLORATORY_EARLY_CHUNK_LOAD_RACE",
        "loader": "21.1.248", "golden_runtime_changed": False,
        "event_handler_calls_world": False,
        "controller_onload_only_readonly_hasChunkAt": True,
        "real_neighbor_unavailable": "NOT_YET_OBSERVED",
        "source_sha256": {key: {"pre":hashlib.sha256(pre[key].encode()).hexdigest(),
                                "post":hashlib.sha256(updated[key].encode()).hexdigest()}
                          for key in pre},
        "e3_profile": evidence,
    }
    (output / "preflight.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def parse_events(raw: str) -> dict:
    chunk_events = [{"phase":m[1],"x":int(m[2]),"z":int(m[3]),"nano":int(m[4])}
                    for m in LOAD_RE.finditer(raw)]
    def states(regex):
        for m in regex.finditer(raw):
            if regex is ONLOAD_RE:
                yield {"tick":int(m[1]),"revision":int(m[2]),
                       "c":m[3]=="true","p":m[4]=="true",
                       "a":m[5]=="true","b":m[6]=="true","nano":int(m[7])}
            else:
                yield {"tick":int(m[1]),"revision":int(m[2]),
                       "validation":m[3],"c":m[4]=="true","p":m[5]=="true",
                       "a":m[6]=="true","b":m[7]=="true","nano":int(m[8])}
    return {"chunk_events":chunk_events,
            "onload":list(states(ONLOAD_RE)),
            "revalidate":list(states(REVALIDATE_RE))}


def physical_gap(s: dict) -> bool:
    return s["c"] and s["p"] and (not s["a"] or not s["b"])


def analyze(project: Path, exit_code: int) -> dict:
    output = project / LOG_REL
    if not (output/"preflight.json").is_file():
        raise e3.TraceBlocked("E4 BLOCKED: E4 generated source provenance not found")
    inherited = e3.analyze(project, exit_code)
    log = project / e3.E1_OUT / "delayed-neighbor-restart.log"
    if not log.is_file():
        raise e3.TraceBlocked("E4 BLOCKED: restart phase log unavailable")
    parsed = parse_events(log.read_text(encoding="utf-8"))
    onload = parsed["onload"]
    revalidation = parsed["revalidate"]
    missing = [r for r in onload if physical_gap(r)]
    failed_revalidation = [r for r in revalidation if r["validation"] == "UNAVAILABLE"]
    sufficient = (len(parsed["chunk_events"])>=4 and len(onload)>0 and len(revalidation)>0
                  and inherited["result"] != "TRACE_INCOMPLETE")
    verdict = ("INCOMPLETE_EARLY_LIFECYCLE_TRACE" if not sufficient else
               "OBSERVED_REAL_ONLOAD_GAP_REQUIRES_REVIEW" if missing else
               "NO_REAL_ONLOAD_GAP_OBSERVED")
    report = {
        "schema_version":1,"state":verdict,"loader":"21.1.248","e3_result":inherited["result"],
        "experiment_exit_code":exit_code,"chunk_lifecycle_events":parsed["chunk_events"],
        "onload_snapshots":onload,"revalidation_snapshots":revalidation,
        "onload_gap_count":len(missing),"onload_gap_samples":missing,
        "unavailable_revalidate_count":len(failed_revalidation),
        "unavailable_revalidate_samples":failed_revalidation,
        "real_delayed_neighbor_recovery_proven":False,
        "physical_negative_control":"NOT_RUN",
        "physical_two_client_acceptance":"PENDING","p2_threads":"OPEN",
    }
    (output/"result.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare","analyze"))
    parser.add_argument("--project",required=True)
    parser.add_argument("--exit-code",type=int,default=2)
    args=parser.parse_args()
    try:
        project=e3.project_at(args.project)
        result=prepare(project) if args.action=="prepare" else analyze(project,args.exit_code)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0 if args.action=="prepare" or result["state"]!="INCOMPLETE_EARLY_LIFECYCLE_TRACE" else 2
    except (e3.TraceBlocked,e3.base.AcceptanceError,ValueError) as exc:
        print(f"E4 BLOCKED: {exc}")
        return 2


if __name__=="__main__":
    raise SystemExit(main())
