from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from construction.core import build_ir as c2
from construction.core import modded_palette as c5
from construction.core import modpack_registry as c4

from .artifacts import ArtifactStore
from .errors import C9Error


_QUERY_RE = re.compile(r"^[a-z0-9_.:/-]+$")
_NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")
_AUTHORITIES = frozenset({"runtime_confirmed", "static_only_unconfirmed"})


class ConstructionFacade:
    """Strict, capability-limited adapters over Construction authorities."""

    def __init__(self, store: ArtifactStore) -> None:
        if not isinstance(store, ArtifactStore):
            raise TypeError("store must be an ArtifactStore")
        self.store = store

    def registry_search(
        self,
        registry: object,
        *,
        query: str | None = None,
        namespace: str | None = None,
        authority: str | None = None,
        safety: list[str] | None = None,
        limit: int = 25,
    ) -> list[dict[str, object]]:
        registry_errors = c4.validate_modpack_registry(registry)
        if registry_errors:
            raise C9Error(
                "AUTHORITY_REJECTED",
                "C4 rejected supplied registry",
                authority="C4",
                details=registry_errors,
            )

        if query is not None and (
            not isinstance(query, str)
            or not query
            or _QUERY_RE.fullmatch(query) is None
        ):
            raise C9Error("INVALID_INPUT", "query must be a non-empty lowercase block-id substring")
        if namespace is not None and (
            not isinstance(namespace, str)
            or _NAMESPACE_RE.fullmatch(namespace) is None
        ):
            raise C9Error("INVALID_INPUT", "namespace must be a lowercase namespace")
        if authority is not None and authority not in _AUTHORITIES:
            raise C9Error("INVALID_INPUT", "authority filter is invalid")
        if safety is not None:
            if not isinstance(safety, list) or not safety:
                raise C9Error("INVALID_INPUT", "safety must be a non-empty list")
            if any(not isinstance(item, str) or item not in c4.SAFETY_CLASSES for item in safety):
                raise C9Error("INVALID_INPUT", "safety contains an invalid C4 safety class")
            if len(safety) != len(set(safety)):
                raise C9Error("INVALID_INPUT", "safety classes must be unique")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise C9Error("INVALID_INPUT", "limit must be an integer from 1 through 100")

        safety_filter = set(safety) if safety is not None else None
        matches: list[dict[str, object]] = []
        for block in registry["blocks"]:  # type: ignore[index]
            block_id = block["id"]
            block_namespace = block_id.split(":", 1)[0]
            if query is not None and query not in block_id:
                continue
            if namespace is not None and block_namespace != namespace:
                continue
            if authority is not None and block["authority"] != authority:
                continue
            if safety_filter is not None and block["safety"] not in safety_filter:
                continue
            matches.append(
                {
                    "id": block_id,
                    "namespace": block_namespace,
                    "available": block["available"],
                    "authority": block["authority"],
                    "safety": block["safety"],
                    "state_count": len(block["states"]),
                }
            )

        matches.sort(key=lambda item: str(item["id"]))
        return matches[:limit]

    def palette_resolve(
        self,
        build_spec: object,
        registry: object,
        request: object,
    ) -> dict[str, object]:
        try:
            return c5.resolve_palette(build_spec, registry, request)
        except c5.PaletteResolutionError as exc:
            raise C9Error(
                "AUTHORITY_REJECTED",
                "C5 rejected palette resolution input",
                authority="C5",
                details=[str(exc)],
            ) from None

    def build_canonicalize(
        self,
        build_spec: dict[str, Any],
        placements: list[dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            return c2.canonicalize_build_ir(
                build_spec,
                placements,
                producer="construction-c9-mcp",
                producer_version="c9-mcp-v1",
            )
        except c2.BuildIRError as exc:
            raise C9Error(
                "AUTHORITY_REJECTED",
                "C2 rejected canonicalization input",
                authority="C2",
                details=[str(exc)],
            ) from None

    def build_validate(self, build_ir: object) -> dict[str, object]:
        errors = c2.validate_build_ir(build_ir)
        return {"valid": not errors, "errors": errors}

    def build_edit(
        self,
        build_spec: dict[str, Any],
        build_ir: object,
        operations: object,
    ) -> dict[str, Any]:
        ir_errors = c2.validate_build_ir(build_ir)
        if ir_errors:
            raise C9Error(
                "AUTHORITY_REJECTED",
                "C2 rejected supplied Build IR",
                authority="C2",
                details=ir_errors,
            )

        try:
            build_spec_sha256 = c2.build_spec_fingerprint(build_spec)
        except c2.BuildIRError as exc:
            raise C9Error(
                "AUTHORITY_REJECTED",
                "C2 rejected supplied BuildSpec",
                authority="C2",
                details=[str(exc)],
            ) from None

        canonical_ir = build_ir  # C2 validation above guarantees the shape used below.
        metadata = canonical_ir["metadata"]  # type: ignore[index]
        if metadata["build_spec_sha256"] != build_spec_sha256:
            raise C9Error(
                "AUTHORITY_REJECTED",
                "BuildSpec fingerprint does not match the supplied Build IR",
                authority="C2",
                details=["metadata.build_spec_sha256 does not match supplied BuildSpec"],
            )

        if not isinstance(operations, list) or not operations:
            raise C9Error("INVALID_INPUT", "operations must be a non-empty list")

        palette = canonical_ir["palette"]  # type: ignore[index]
        blocks = canonical_ir["blocks"]  # type: ignore[index]
        current: dict[tuple[int, int, int], dict[str, Any]] = {
            (block["x"], block["y"], block["z"]): deepcopy(palette[block["palette_index"]])
            for block in blocks
        }
        size = canonical_ir["bounds"]["size"]  # type: ignore[index]
        touched: set[tuple[int, int, int]] = set()

        for index, operation in enumerate(operations):
            if not isinstance(operation, dict):
                raise C9Error("INVALID_INPUT", f"operations[{index}] must be an object")

            op = operation.get("op")
            if op == "set_block":
                expected_fields = {"op", "x", "y", "z", "block_state"}
            elif op == "remove_block":
                expected_fields = {"op", "x", "y", "z"}
            else:
                raise C9Error("INVALID_INPUT", f"operations[{index}].op is invalid")

            if set(operation) != expected_fields:
                raise C9Error(
                    "INVALID_INPUT",
                    f"operations[{index}] fields do not match the {op} contract",
                )

            coordinates: list[int] = []
            for axis in ("x", "y", "z"):
                value = operation[axis]
                if isinstance(value, bool) or not isinstance(value, int):
                    raise C9Error(
                        "INVALID_INPUT",
                        f"operations[{index}].{axis} must be an integer",
                    )
                if value < 0 or value >= size[axis]:
                    raise C9Error(
                        "INVALID_INPUT",
                        f"operations[{index}].{axis} is out of bounds",
                    )
                coordinates.append(value)

            coordinate = (coordinates[0], coordinates[1], coordinates[2])
            if coordinate in touched:
                raise C9Error("INVALID_INPUT", f"coordinate {coordinate} is touched more than once")
            touched.add(coordinate)

            if op == "set_block":
                block_state = operation["block_state"]
                try:
                    c2.canonical_block_state_string(block_state)
                except (c2.BuildIRError, TypeError) as exc:
                    raise C9Error(
                        "INVALID_INPUT",
                        f"operations[{index}].block_state is invalid",
                        details=[str(exc)],
                    ) from None
                current[coordinate] = deepcopy(block_state)
                continue

            if coordinate not in current:
                raise C9Error(
                    "INVALID_INPUT",
                    f"operations[{index}] cannot remove an absent coordinate",
                )
            del current[coordinate]

        placements = [
            {
                "x": coordinate[0],
                "y": coordinate[1],
                "z": coordinate[2],
                "block_state": deepcopy(block_state),
            }
            for coordinate, block_state in sorted(current.items())
        ]

        try:
            return c2.canonicalize_build_ir(
                build_spec,
                placements,
                producer="construction-c9-edit",
                producer_version="c9-mcp-v1",
            )
        except c2.BuildIRError as exc:
            raise C9Error(
                "AUTHORITY_REJECTED",
                "C2 rejected edited Build IR",
                authority="C2",
                details=[str(exc)],
            ) from None
