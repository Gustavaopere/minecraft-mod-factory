"""E4 read-only early-onLoad instrumentation and fail-closed evidence classification."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"engineering/tests/experiments/i10_e4_onload_boundary_trace_248.py"
GOLDEN=ROOT/"engineering/tests/golden/i10-multiblock-foundation/overlay"
TEMPLATE=ROOT/"engineering/templates/neoforge-mod"


def get_module():
    spec=importlib.util.spec_from_file_location("i10_e4_onload_boundary_trace_248",SCRIPT)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fresh_fixture(tmp: str):
    project=Path(tmp)/".factory-ci/i10/generated"
    p=project/"src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlockEntity.java"
    p.parent.mkdir(parents=True)
    golden=GOLDEN/"src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlockEntity.java"
    p.write_text(golden.read_text())
    (project/"gradle.properties").write_text((TEMPLATE/"gradle.properties.tmpl").read_text())
    (project/"gradle.lockfile").write_text((TEMPLATE/"gradle.lockfile.tmpl").read_text())
    return project


class E4EarlyLifecycleTraceTests(unittest.TestCase):
    def test_generated_only_instrumentation_and_exact_profile(self):
        e4=get_module()
        golden=GOLDEN/"src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlockEntity.java"
        original=golden.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            project=fresh_fixture(tmp)
            manifest=e4.prepare(project)
            self.assertEqual("21.1.248",manifest["loader"])
            self.assertFalse(manifest["golden_runtime_changed"])
            self.assertFalse(manifest["event_handler_calls_world"])
            self.assertEqual(original,golden.read_bytes())
            controller=(project/e4.CONTROLLER).read_text()
            observer=(project/e4.e3.OBS_REL).read_text()
            self.assertIn("I10_E4_ONLOAD",controller)
            self.assertIn("I10_E4_REVALIDATE",controller)
            self.assertIn("ChunkEvent.Load",observer)
            self.assertIn("ChunkEvent.Unload",observer)
            block=observer.split("public static void onLoad(ChunkEvent.Load event)",1)[1].split(
                "@SubscribeEvent",1)[0]
            for forbidden in ("event.getLevel(", "level.hasChunkAt(", "getChunk(", "getCapability("):
                if forbidden=="getChunk(":
                    self.assertEqual(1,block.count("getChunk().getPos()"))
                else:
                    self.assertNotIn(forbidden,block)
            self.assertIn("neo_version=21.1.248",(project/"gradle.properties").read_text())
            with self.assertRaisesRegex(e4.e3.TraceBlocked,"existing world"):
                e4.prepare(project)

    def test_early_load_gap_and_no_gap_classification_are_distinct(self):
        e4=get_module()
        log=(
            "I10_E4_CHUNK phase=load x=9 z=10 nano=100\n"
            "I10_E4_CHUNK phase=load x=10 z=10 nano=101\n"
            "I10_E4_CHUNK phase=load x=9 z=9 nano=105\n"
            "I10_E4_CHUNK phase=load x=10 z=9 nano=106\n"
            "I10_E4_ONLOAD tick=72 revision=1 c=true p=true a=false b=true nano=103\n"
            "I10_E4_REVALIDATE tick=73 revision=1 validation=UNAVAILABLE c=true p=true a=false b=true nano=104\n"
        )
        parsed=e4.parse_events(log)
        self.assertEqual(4,len(parsed["chunk_events"]))
        self.assertEqual(1,len(parsed["onload"]))
        self.assertTrue(e4.physical_gap(parsed["onload"][0]))
        self.assertEqual("UNAVAILABLE",parsed["revalidate"][0]["validation"])
        self.assertFalse(e4.physical_gap({"c":True,"p":False,"a":False,"b":True}))

    def test_analyze_fail_closed_and_reports_bounded_observation(self):
        e4=get_module()
        with tempfile.TemporaryDirectory() as tmp:
            project=fresh_fixture(tmp)
            e4.prepare(project)
            output=project/e4.e3.E1_OUT
            output.mkdir(parents=True)
            (output/"delayed-neighbor-restart.log").write_text(
                "I10_E4_CHUNK phase=load x=9 z=10 nano=100\n"
                "I10_E4_CHUNK phase=load x=10 z=10 nano=101\n"
                "I10_E4_CHUNK phase=load x=9 z=9 nano=105\n"
                "I10_E4_CHUNK phase=load x=10 z=9 nano=106\n"
                "I10_E4_ONLOAD tick=72 revision=1 c=true p=true a=false b=true nano=103\n"
                "I10_E4_REVALIDATE tick=73 revision=1 validation=UNAVAILABLE c=true p=true a=false b=true nano=104\n")
            with mock.patch.object(e4.e3,"analyze",return_value={"result":"OBSERVED_REAL_PARTIAL_AVAILABILITY_NEEDS_REVIEW"}):
                r=e4.analyze(project,2)
            self.assertEqual("OBSERVED_REAL_ONLOAD_GAP_REQUIRES_REVIEW",r["state"])
            self.assertEqual(1,r["onload_gap_count"])
            self.assertEqual(1,r["unavailable_revalidate_count"])
            self.assertFalse(r["real_delayed_neighbor_recovery_proven"])
            self.assertEqual(r["state"],json.loads((project/e4.LOG_REL/"result.json").read_text())["state"])
            no_events=project/e4.e3.E1_OUT/"delayed-neighbor-restart.log"
            no_events.write_text("I10_E4_ONLOAD tick=70 revision=1 c=true p=true a=true b=true nano=100\n")
            with mock.patch.object(e4.e3,"analyze",return_value={"result":"OBSERVED_ALL_ADJACENT_CHUNKS_LOADED"}):
                r=e4.analyze(project,2)
            self.assertEqual("INCOMPLETE_EARLY_LIFECYCLE_TRACE",r["state"])

    def test_existing_world_or_foreign_output_blocked(self):
        e4=get_module()
        with tempfile.TemporaryDirectory() as tmp:
            project=fresh_fixture(tmp)
            (project/"run/server/world").mkdir(parents=True)
            with self.assertRaisesRegex(e4.e3.TraceBlocked,"existing world"):
                e4.prepare(project)

    def test_anchor_drift_fails_closed(self):
        e4=get_module()
        with self.assertRaises(e4.e3.TraceBlocked):
            e4.anchored("X X","X","Y")
        with self.assertRaises(e4.e3.TraceBlocked):
            e4.anchored("NO","X","Y")


if __name__=="__main__":
    unittest.main()
