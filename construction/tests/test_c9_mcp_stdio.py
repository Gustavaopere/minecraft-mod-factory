from __future__ import annotations

import asyncio
import base64
import json
import sys
import unittest
from contextlib import asynccontextmanager
from pathlib import Path

import mcp.types as types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from construction.core import sponge_v3 as c6


ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = ROOT / "construction" / "mcp" / "server.py"
GOLDEN = ROOT / "construction" / "fixtures" / "vanilla-golden"
C8_GOLDEN = GOLDEN / "c8"
VIEW_IDS = ("front", "back", "left", "right", "top", "isometric", "layers")
TOOL_NAMES = (
    "registry_search",
    "palette_resolve",
    "build_canonicalize",
    "build_validate",
    "build_edit",
    "qa_structural",
    "preview_render",
    "qa_visual",
    "export_sponge_v3",
)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


@asynccontextmanager
async def _session():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


class C9MCPStdioTests(unittest.IsolatedAsyncioTestCase):
    def _tool_json(self, result: types.CallToolResult):
        self.assertFalse(result.is_error)
        self.assertIsNone(result.structured_content)
        self.assertEqual(len(result.content), 1)
        block = result.content[0]
        self.assertIsInstance(block, types.TextContent)
        return json.loads(block.text)

    def _blob_bytes(self, result: types.ReadResourceResult) -> bytes:
        self.assertEqual(len(result.contents), 1)
        block = result.contents[0]
        self.assertIsInstance(block, types.BlobResourceContents)
        return base64.b64decode(block.blob, validate=True)

    async def test_real_stdio_discovery_and_tool_call(self) -> None:
        build_ir = _load_json(GOLDEN / "expected-build-ir.json")
        async with _session() as session:
            tools = await session.list_tools()
            self.assertEqual(tuple(tool.name for tool in tools.tools), TOOL_NAMES)

            prompts = await session.list_prompts()
            self.assertEqual(prompts.prompts, [])
            resources = await session.list_resources()
            self.assertEqual(resources.resources, [])
            templates = await session.list_resource_templates()
            self.assertEqual(len(templates.resource_templates), 1)
            self.assertEqual(
                str(templates.resource_templates[0].uri_template),
                "construction://artifact/sha256/{digest}",
            )

            result = await session.call_tool("build_validate", arguments={"build_ir": build_ir})
            self.assertEqual(self._tool_json(result), {"valid": True, "errors": []})

            malformed = await session.call_tool(
                "build_validate",
                arguments={"build_ir": build_ir, "extra": "must-be-rejected"},
            )
            self.assertTrue(malformed.is_error)
            self.assertIsNone(malformed.structured_content)
            self.assertEqual(len(malformed.content), 1)
            self.assertIsInstance(malformed.content[0], types.TextContent)
            self.assertIn("extra", malformed.content[0].text.lower())

    async def test_real_stdio_resource_read(self) -> None:
        build_ir = _load_json(GOLDEN / "expected-build-ir.json")
        async with _session() as session:
            preview = self._tool_json(
                await session.call_tool("preview_render", arguments={"build_ir": build_ir})
            )
            front = next(item for item in preview["views"] if item["id"] == "front")
            resource = await session.read_resource(front["uri"])
            self.assertEqual(
                self._blob_bytes(resource),
                (C8_GOLDEN / "front.svg").read_bytes(),
            )

    async def test_real_stdio_golden_flow(self) -> None:
        build_spec = _load_json(GOLDEN / "build-spec.json")
        build_ir = _load_json(GOLDEN / "expected-build-ir.json")
        review = _load_json(C8_GOLDEN / "review-evidence.json")
        expected_report = _load_json(C8_GOLDEN / "expected-visual-qa-report.json")

        async with _session() as session:
            validation = self._tool_json(
                await session.call_tool("build_validate", arguments={"build_ir": build_ir})
            )
            self.assertEqual(validation, {"valid": True, "errors": []})

            preview = self._tool_json(
                await session.call_tool("preview_render", arguments={"build_ir": build_ir})
            )
            self.assertEqual(tuple(item["id"] for item in preview["views"]), VIEW_IDS)
            for descriptor in preview["views"]:
                with self.subTest(view=descriptor["id"]):
                    resource = await session.read_resource(descriptor["uri"])
                    self.assertEqual(
                        self._blob_bytes(resource),
                        (C8_GOLDEN / f"{descriptor['id']}.svg").read_bytes(),
                    )

            report = self._tool_json(
                await session.call_tool(
                    "qa_visual",
                    arguments={
                        "build_spec": build_spec,
                        "build_ir": build_ir,
                        "preview_bundle_uri": preview["bundle_uri"],
                        "review_evidence": review,
                    },
                )
            )
            self.assertEqual(report, expected_report)
            self.assertEqual(
                _canonical_json_bytes(report),
                (C8_GOLDEN / "expected-visual-qa-report.json").read_bytes(),
            )

            exported = self._tool_json(
                await session.call_tool(
                    "export_sponge_v3",
                    arguments={"build_ir": build_ir, "required_mods": []},
                )
            )
            self.assertEqual(exported["artifact_kind"], "sponge_v3")
            schem = self._blob_bytes(await session.read_resource(exported["uri"]))
            self.assertEqual(c6.validate_sponge_v3(schem), [])

    async def test_stdio_server_terminates_cleanly(self) -> None:
        async def roundtrip() -> None:
            async with _session() as session:
                tools = await session.list_tools()
                self.assertEqual(len(tools.tools), 9)

        await asyncio.wait_for(roundtrip(), timeout=15.0)


if __name__ == "__main__":
    unittest.main()
