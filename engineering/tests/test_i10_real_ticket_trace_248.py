"""E3 fail-closed fixture-only source profile and read-only server trace tests."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOL=ROOT/"engineering/tests/experiments/i10_real_ticket_trace_248.py"
TEMPLATES=ROOT/"engineering/templates/neoforge-mod"


def e3():
    assert TOOL.is_file(), "E3 RED: real ticket trace script missing"
    spec=importlib.util.spec_from_file_location("i10_real_ticket_trace_248",TOOL)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp: str, *, source_version: str = "21.1.250"):
    p=Path(tmp)/".factory-ci/i10/generated"
    p.mkdir(parents=True)
    (p/"gradle.properties").write_text((TEMPLATES/"gradle.properties.tmpl").read_text())
    (p/"gradle.lockfile").write_text((TEMPLATES/"gradle.lockfile.tmpl").read_text())
    return p


class I10RealTicketTraceContract(unittest.TestCase):
    def test_profile_is_converted_using_existing_explicit_factory_scaffold(self):
        m=e3()
        with tempfile.TemporaryDirectory() as tmp:
            project=fixture(tmp)
            original_lock=(project/"gradle.lockfile").read_bytes()
            self.assertEqual(project,m.project_at(project,Path(tmp)))
            result=m.prepare(project)
            self.assertTrue(result["observer_only"])
            self.assertTrue(result["no_capability_query"])
            self.assertEqual("21.1.248",result["physical_modlist_neoforge"])
            self.assertIn("neo_version=21.1.248",(project/"gradle.properties").read_text())
            changed=(project/"gradle.lockfile").read_text()
            self.assertNotEqual(original_lock,(project/"gradle.lockfile").read_bytes())
            self.assertIn("net.neoforged:neoforge:21.1.248=sdk,testSdk",changed)
            self.assertIn("net.neoforged.fancymodloader:loader:4.0.43=",changed)
            observer=(project/m.OBS_REL).read_text()
            self.assertIn("ChunkTicketLevelUpdatedEvent",observer)
            self.assertIn("LevelTickEvent.Post",observer)
            self.assertIn("level.hasChunkAt(CASING_A)",observer)
            self.assertNotIn("getCapability(",observer)
            self.assertNotIn("setChunkForced(",observer)
            self.assertNotIn("getChunk(",observer)
            self.assertEqual(result["observer_java_sha256"],__import__("hashlib").sha256(observer.encode()).hexdigest())
            with self.assertRaisesRegex(m.TraceBlocked,"existing world, observer"):
                m.prepare(project)

    def test_scope_and_wrong_profile_fail_closed(self):
        m=e3()
        with tempfile.TemporaryDirectory() as tmp:
            project=fixture(tmp)
            with self.assertRaisesRegex(m.TraceBlocked,"disposable"):
                m.project_at(project.parent,Path(tmp))
            file=project/"gradle.properties"
            file.write_text(file.read_text().replace("neo_version=21.1.250","neo_version=21.1.247"))
            with self.assertRaisesRegex(m.TraceBlocked,"expected canonical"):
                m.prepare(project)

    def test_parser_differentiates_real_tick_availability_from_ticket_updates(self):
        m=e3()
        with tempfile.TemporaryDirectory() as tmp:
            project=fixture(tmp)
            m.prepare(project)
            folder=project/m.E1_OUT
            folder.mkdir(parents=True)
            (folder/"prepare-full-unload.log").write_text("phase finished\n")
            (folder/"delayed-neighbor-restart.log").write_text(
                "I10_TICKET x=9 z=9 old=46 new=32 tick=64\n"
                "I10_TICKET x=10 z=9 old=46 new=32 tick=64\n"
                "I10_TICKET x=9 z=10 old=46 new=31 tick=64\n"
                "I10_TICKET x=10 z=10 old=46 new=31 tick=64\n"
                "I10_CHUNK_TICK tick=65 c=true p=true a=true b=true\n"
                "I10_PEEK action=peek validation=VALID runtime=FORMED revision=1\n")
            result=m.analyze(project,2)
            self.assertEqual("OBSERVED_ALL_ADJACENT_CHUNKS_LOADED",result["result"])
            self.assertEqual(4,result["ticket_event_count"])
            self.assertEqual(0,result["sampled_missing_count"])
            self.assertEqual(0,result["unavailable_peek_count"])
            self.assertFalse(result["physical_chunk_race_proven"])
            file=folder/"delayed-neighbor-restart.log"
            file.write_text(file.read_text().replace("a=true b=true","a=false b=true")
                            .replace("validation=VALID","validation=UNAVAILABLE"))
            result=m.analyze(project,0)
            self.assertEqual("OBSERVED_REAL_PARTIAL_AVAILABILITY_NEEDS_REVIEW",result["result"])
            self.assertEqual(1,result["sampled_missing_count"])
            self.assertTrue(result["physical_chunk_race_proven"])

    def test_absent_events_do_not_pass(self):
        m=e3()
        with tempfile.TemporaryDirectory() as tmp:
            project=fixture(tmp)
            m.prepare(project)
            folder=project/m.E1_OUT
            folder.mkdir(parents=True)
            (folder/"prepare-full-unload.log").write_text("phase1")
            (folder/"delayed-neighbor-restart.log").write_text("I10_PEEK action=peek validation=VALID runtime=FORMED revision=1\n")
            result=m.analyze(project,2)
            self.assertEqual("TRACE_INCOMPLETE",result["result"])
            self.assertEqual(0,result["ticket_event_count"])
            (folder/"delayed-neighbor-restart.log").unlink()
            with self.assertRaisesRegex(m.TraceBlocked,"both dedicated-server"):
                m.analyze(project,2)


if __name__=="__main__":
    unittest.main()
