#!/usr/bin/env python3
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

REQUIRED = [
    "engineering/README.md",
    "engineering/REPO-ROUTING.md",
    "engineering/AGENT-WORKFLOW.md",
    "engineering/DIAGNOSTICS.md",
    "engineering/TESTING.md",
    "engineering/catalog/sources/SOURCE-REGISTRY.json",
    "skills/README.md",
    "skills/ROUTER.md",
    "skills/VERSION-AUTHORITY.md",
    "skills/USER-GUIDED-WORKFLOW.md",
    "migration/MIGRATION-MATRIX-F1-M3.md",
    "plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md",
    "plans/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md",
]

PLAN_HASHES = {
    "plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md": "29fc7f4b949b2b8dba327eb3f022f4cd84b11a352430ca821bdaec13072b8744",
    "plans/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md": "723bb083d5b646812cd44a03a1ef50e8505b366923b64aba5931ee4b7b63befb",
}

errors = []
for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        errors.append(f"missing required file: {rel}")

for rel, expected in PLAN_HASHES.items():
    path = ROOT / rel
    if path.is_file():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"canonical plan hash mismatch: {rel}: {actual}")

registry_path = ROOT / "engineering/catalog/sources/SOURCE-REGISTRY.json"
if registry_path.is_file():
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        sources = {item["source_id"]: item for item in registry.get("sources", [])}
        for source_id, authority_root in (
            ("integration_control_plane", "engineering/"),
            ("repo_textura", "art/"),
        ):
            item = sources.get(source_id)
            if not item:
                errors.append(f"missing source registry entry: {source_id}")
                continue
            locator = item.get("locator", {})
            if item.get("state") != "CONFIRMED":
                errors.append(f"source not CONFIRMED: {source_id}")
            if locator.get("repository_full_name") != "Gustavaopere/minecraft-mod-factory":
                errors.append(f"wrong Factory repository binding: {source_id}")
            if locator.get("authority_root") != authority_root:
                errors.append(f"wrong authority root for {source_id}: {locator.get('authority_root')}")
    except (ValueError, KeyError, TypeError) as exc:
        errors.append(f"invalid source registry: {exc}")

version_path = ROOT / "skills/VERSION-AUTHORITY.md"
if version_path.is_file():
    version_text = version_path.read_text(encoding="utf-8")
    for token in ("Minecraft: **1.21.1**", "NeoForge: **21.1.248**", "Java: **21**", "modlist física"):
        if token not in version_text:
            errors.append(f"version authority missing token: {token}")

routing_path = ROOT / "engineering/REPO-ROUTING.md"
if routing_path.is_file():
    routing = routing_path.read_text(encoding="utf-8")
    for token in ("Gustavaopere/minecraft-mod-factory", "engineering/", "art/", "runtime authority"):
        if token not in routing:
            errors.append(f"routing contract missing token: {token}")
    forbidden = "Gustavaopere/neoforge-rpg-skilltree` is the canonical integration/control-plane repository"
    if forbidden in routing:
        errors.append("routing contract still assigns control-plane authority to the RPG repository")

diagnostics_path = ROOT / "engineering/DIAGNOSTICS.md"
if diagnostics_path.is_file():
    diagnostics = diagnostics_path.read_text(encoding="utf-8")
    if "[mod-factory/<domain>/<event>]" not in diagnostics:
        errors.append("Factory diagnostics prefix missing")
    if "[rpgskilltree/" in diagnostics:
        errors.append("RPG runtime diagnostics leaked into Factory contract")

if errors:
    for error in errors:
        print(f"ERROR: {error}")
    sys.exit(1)

print("E1/S1 governance validation: PASS")
