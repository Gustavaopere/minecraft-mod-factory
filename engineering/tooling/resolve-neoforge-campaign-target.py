#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.request

MAVEN_METADATA_URL = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
MINECRAFT_NEOFORGE_LINES = {
    "1.21.1": "21.1",
}
STABLE_VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
VERSION_PATH = ("metadata", "versioning", "versions", "version")
_XML_DECL_RE = re.compile(
    r"<\?xml\s+version\s*=\s*(['\"])1\.0\1"
    r"(?:\s+encoding\s*=\s*(['\"])UTF-8\2)?"
    r"(?:\s+standalone\s*=\s*(['\"])(?:yes|no)\3)?\s*\?>",
    re.IGNORECASE,
)
_SIMPLE_TAG_RE = re.compile(r"(?P<closing>/)?(?P<name>[A-Za-z_][A-Za-z0-9_.:-]*)\s*")


def _invalid_metadata(reason: str) -> ValueError:
    return ValueError(f"invalid NeoForge Maven metadata XML: {reason}")


def parse_maven_versions(metadata_xml: str) -> list[str]:
    """Extract Maven versions without feeding remote content into an entity-capable parser."""
    text = metadata_xml.lstrip("\ufeff")
    cursor = len(text) - len(text.lstrip())

    if text.startswith("<?xml", cursor):
        declaration_end = text.find("?>", cursor + 5)
        if declaration_end < 0:
            raise _invalid_metadata("unterminated XML declaration")
        declaration = text[cursor : declaration_end + 2]
        if _XML_DECL_RE.fullmatch(declaration) is None:
            raise ValueError("unsafe XML declaration in NeoForge Maven metadata")
        text = text[:cursor] + text[declaration_end + 2 :]

    if "<!" in text or "<?" in text or "&" in text:
        raise ValueError("unsafe XML declaration in NeoForge Maven metadata")

    versions: list[str] = []
    path: list[str] = []
    version_text: list[str] = []
    root_seen = False
    root_closed = False
    cursor = 0

    while cursor < len(text):
        if text[cursor] != "<":
            next_tag = text.find("<", cursor)
            if next_tag < 0:
                next_tag = len(text)
            chunk = text[cursor:next_tag]
            if not path and chunk.strip():
                raise _invalid_metadata("non-whitespace text outside metadata root")
            if tuple(path) == VERSION_PATH:
                version_text.append(chunk)
            cursor = next_tag
            continue

        tag_end = text.find(">", cursor + 1)
        if tag_end < 0:
            raise _invalid_metadata("unterminated tag")
        raw_tag = text[cursor + 1 : tag_end]
        match = _SIMPLE_TAG_RE.fullmatch(raw_tag)
        if match is None:
            raise _invalid_metadata("attributes, self-closing tags, or malformed tags are not accepted")

        name = match.group("name")
        closing = match.group("closing") is not None

        if closing:
            if not path or path[-1] != name:
                raise _invalid_metadata(f"mismatched closing tag: {name}")
            if tuple(path) == VERSION_PATH:
                value = "".join(version_text).strip()
                if value:
                    versions.append(value)
                version_text.clear()
            path.pop()
            if not path:
                if name != "metadata":
                    raise _invalid_metadata("root element must be metadata")
                root_closed = True
        else:
            if root_closed:
                raise _invalid_metadata("multiple root elements")
            if not path:
                if root_seen or name != "metadata":
                    raise _invalid_metadata("root element must be metadata")
                root_seen = True
            elif tuple(path) == VERSION_PATH:
                raise _invalid_metadata("version elements cannot contain child markup")
            path.append(name)
            if tuple(path) == VERSION_PATH:
                version_text.clear()

        cursor = tag_end + 1

    if path:
        raise _invalid_metadata(f"unclosed tag: {path[-1]}")
    if not root_seen or not root_closed:
        raise _invalid_metadata("metadata root is missing or incomplete")
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
    args = parser.parse_args()

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
