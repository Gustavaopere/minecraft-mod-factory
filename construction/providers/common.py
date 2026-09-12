from __future__ import annotations

import hashlib
import json
import re

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PROVIDER_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SOURCE_REF_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

CAPABILITIES = (
    "IMAGE_TO_STRUCTURE",
    "LITEMATIC_EXPORT",
    "LITEMATIC_IMPORT",
    "MESH_TO_STRUCTURE",
    "PROMPT_TO_STRUCTURE",
    "SCHEMATIC_EXPORT",
    "SCHEMATIC_IMPORT",
    "STRUCTURE_EDITING",
    "VANILLA_STRUCTURE_EXPORT",
    "VANILLA_STRUCTURE_IMPORT",
)
ARTIFACT_KINDS = (
    "BEDROCK_MCSTRUCTURE",
    "IMAGE",
    "LITEMATIC_FILE",
    "MESH",
    "SCHEMATIC_FILE",
    "VANILLA_STRUCTURE_NBT",
    "WORLD_ZIP",
)
PROOF_LEVELS = (
    "EP0_DISCOVERED",
    "EP1_HANDOFF_VERIFIED",
    "EP2_EXECUTION_PROVEN",
    "EP3_FORMAT_VALIDATED",
    "EP4_FACTORY_INTEGRATION_VALIDATED",
    "EP5_GOLDEN_VALIDATED",
)
API_STATES = (
    "UNVERIFIED_API",
    "VERIFIED_API",
    "CONTRACT_PROVEN_API",
    "SMOKE_PROVEN_API",
)
INTEGRATION_MODES = (
    "RESEARCH_ONLY",
    "MANUAL_FILE_HANDOFF",
    "API_ADAPTER",
)
EVIDENCE_KINDS = (
    "FACTORY_TEST",
    "MANUAL_SMOKE",
    "OFFICIAL_DOCS",
    "OFFICIAL_SITE",
    "OFFICIAL_SOURCE",
)
API_AUTH = ("API_KEY", "NONE", "OAUTH", "SESSION", "UNKNOWN")
API_CONTRACT_KINDS = ("GRAPHQL", "OTHER", "REST", "SDK")
DETERMINISM = ("NO", "UNKNOWN", "YES")


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_sorted_unique_strings(values: object, *, allowed: tuple[str, ...] | None = None) -> bool:
    if not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
        return False
    if values != sorted(values) or len(values) != len(set(values)):
        return False
    return allowed is None or all(item in allowed for item in values)


def is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
