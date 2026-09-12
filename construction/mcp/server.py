from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field, StrictInt

if __package__ in {None, ""}:  # Support the canonical direct-script stdio entrypoint.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from construction.mcp.artifacts import ArtifactStore
from construction.mcp.errors import C9Error
from construction.mcp.facade import ConstructionFacade


SERVER_VERSION = "c9-mcp-v1"
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
_INTERNAL_ERROR_JSON = '{"code":"INTERNAL_ERROR","message":"internal C9 failure"}'


class Placement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: StrictInt
    y: StrictInt
    z: StrictInt
    block_state: dict[str, object]


class SetBlockOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["set_block"]
    x: StrictInt
    y: StrictInt
    z: StrictInt
    block_state: dict[str, object]


class RemoveBlockOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["remove_block"]
    x: StrictInt
    y: StrictInt
    z: StrictInt


BuildEditOperation = Annotated[
    SetBlockOperation | RemoveBlockOperation,
    Field(discriminator="op"),
]


STORE = ArtifactStore()
FACADE = ConstructionFacade(STORE)
mcp = MCPServer("Minecraft Construction Factory", version=SERVER_VERSION)


def _canonical_error_payload(error: C9Error) -> str:
    return json.dumps(
        error.payload(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _invoke(operation, /, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except C9Error as exc:
        raise ToolError(_canonical_error_payload(exc)) from None
    except Exception:
        print("C9 internal tool failure", file=sys.stderr)
        raise ToolError(_INTERNAL_ERROR_JSON) from None


@mcp.tool(structured_output=False)
def registry_search(
    registry: dict[str, Any],
    query: str | None = None,
    namespace: str | None = None,
    authority: Literal["runtime_confirmed", "static_only_unconfirmed"] | None = None,
    safety: list[str] | None = None,
    limit: StrictInt = 25,
) -> list[dict[str, object]]:
    return _invoke(
        FACADE.registry_search,
        registry,
        query=query,
        namespace=namespace,
        authority=authority,
        safety=safety,
        limit=limit,
    )


@mcp.tool(structured_output=False)
def palette_resolve(
    build_spec: dict[str, Any],
    registry: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, object]:
    return _invoke(FACADE.palette_resolve, build_spec, registry, request)


@mcp.tool(structured_output=False)
def build_canonicalize(
    build_spec: dict[str, Any],
    placements: list[Placement],
) -> dict[str, Any]:
    return _invoke(
        FACADE.build_canonicalize,
        build_spec,
        [placement.model_dump(mode="python") for placement in placements],
    )


@mcp.tool(structured_output=False)
def build_validate(build_ir: dict[str, Any]) -> dict[str, object]:
    return _invoke(FACADE.build_validate, build_ir)


@mcp.tool(structured_output=False)
def build_edit(
    build_spec: dict[str, Any],
    build_ir: dict[str, Any],
    operations: list[BuildEditOperation],
) -> dict[str, Any]:
    return _invoke(
        FACADE.build_edit,
        build_spec,
        build_ir,
        [operation.model_dump(mode="python") for operation in operations],
    )


@mcp.tool(structured_output=False)
def qa_structural(
    build_spec: dict[str, Any],
    build_ir: dict[str, Any],
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _invoke(FACADE.qa_structural, build_spec, build_ir, registry)


@mcp.tool(structured_output=False)
def preview_render(build_ir: dict[str, Any]) -> dict[str, object]:
    return _invoke(FACADE.preview_render, build_ir)


@mcp.tool(structured_output=False)
def qa_visual(
    build_spec: dict[str, Any],
    build_ir: dict[str, Any],
    preview_bundle_uri: str,
    structural_report: dict[str, Any] | None = None,
    palette_resolution: dict[str, Any] | None = None,
    review_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _invoke(
        FACADE.qa_visual,
        build_spec,
        build_ir,
        preview_bundle_uri,
        structural_report=structural_report,
        palette_resolution=palette_resolution,
        review_evidence=review_evidence,
    )


@mcp.tool(structured_output=False)
def export_sponge_v3(
    build_ir: dict[str, Any],
    required_mods: list[str] | None = None,
) -> dict[str, object]:
    return _invoke(
        FACADE.export_sponge_v3,
        build_ir,
        required_mods=required_mods,
    )


def _close_tool_envelope(name: str) -> None:
    """Make MCP SDK 2.2.0's generated top-level argument model fail closed."""
    tool = mcp._tool_manager.get_tool(name)
    if tool is None:
        raise RuntimeError(f"missing registered C9 tool: {name}")
    generated_model = tool.fn_metadata.arg_model
    config = dict(generated_model.model_config)
    config["extra"] = "forbid"
    closed_model = type(
        f"{generated_model.__name__}Closed",
        (generated_model,),
        {
            "__module__": __name__,
            "model_config": ConfigDict(**config),
        },
    )
    tool.fn_metadata.arg_model = closed_model
    tool.parameters = closed_model.model_json_schema(by_alias=True)


for _tool_name in TOOL_NAMES:
    _close_tool_envelope(_tool_name)


@mcp.resource(
    "construction://artifact/sha256/{digest}",
    mime_type="application/octet-stream",
)
def artifact(digest: str) -> bytes:
    uri = f"construction://artifact/sha256/{digest}"
    return STORE.get(uri).data


if __name__ == "__main__":
    mcp.run()
