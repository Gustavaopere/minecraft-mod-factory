#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

MAVEN_METADATA_URL = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
MINECRAFT_NEOFORGE_LINES = {
    "1.21.1": "21.1",
}
STABLE_VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")


def parse_maven_versions(metadata_xml: str) -> list[str]:
    try:
        root = ET.fromstring(metadata_xml)
    except ET.ParseError as exc:
        raise ValueError(f"invalid NeoForge Maven metadata XML: {exc}") from exc
    versions = []
    for node in root.findall("./versioning/versions/version"):
        if node.text and node.text.strip():
            versions.append(node.text.strip())
    if not versions:
        raise ValueError("NeoForge Maven metadata contains no versions")
    return versions


def select_latest_compatible(versions: list[str], minecraft_version: str) -> str:
    line = MINECRAFT_NEOFORGE_LINES.get(minecraft_version)
    if line is None:
        raise ValueError(f"unsupported Minecraft target for NeoForge resolution: {minecraft_version}")
    prefix = line + "."
    candidates: list[tuple[int, str]] = []
    for value in versions:
        match = STABLE_VERSION_RE.fullmatch(value)
        if match is None or not value.startswith(prefix):
            continue
        candidates.append((int(match.group("patch")), value))
    if not candidates:
        raise ValueError(f"no stable NeoForge release found for Minecraft {minecraft_version} / line {line}.x")
    candidates.sort()
    return candidates[-1][1]


def fetch_official_metadata() -> str:
    request = urllib.request.Request(
        MAVEN_METADATA_URL,
        headers={"User-Agent": "minecraft-mod-factory-neoforge-target-resolver/1"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def resolve_latest(minecraft_version: str) -> str:
    return select_latest_compatible(parse_maven_versions(fetch_official_metadata()), minecraft_version)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve the latest stable NeoForge release compatible with a supported Minecraft campaign target."
    )
    parser.add_argument("--minecraft", default="1.21.1")
    parser.add_argument(
        "--metadata-file",
        help="Optional local Maven metadata XML for deterministic/offline verification instead of network resolution.",
    )
    args = parser.parse_args()

    if args.metadata_file:
        with open(args.metadata_file, "r", encoding="utf-8") as handle:
            versions = parse_maven_versions(handle.read())
        version = select_latest_compatible(versions, args.minecraft)
    else:
        version = resolve_latest(args.minecraft)

    line = MINECRAFT_NEOFORGE_LINES[args.minecraft]
    print(
        json.dumps(
            {
                "minecraft": args.minecraft,
                "loader": "neoforge",
                "neoforge_line": line,
                "neoforge": version,
                "resolution_policy": "latest-compatible-at-campaign-start",
                "resolution_source": MAVEN_METADATA_URL,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
