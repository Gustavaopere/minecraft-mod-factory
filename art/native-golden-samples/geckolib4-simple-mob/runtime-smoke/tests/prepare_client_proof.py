#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent
SMOKE_ROOT = FIXTURES.parent
CLIENT_CONTRACT = SMOKE_ROOT / "client-contract.json"
SERVER_CONTRACT = SMOKE_ROOT / "contract.json"

EXPECTED_CLIENT_TARGET = {
    "minecraft": "1.21.1",
    "neoforge": "21.1.248",
    "java": 21,
    "geckolib": "4.9.2",
}


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def prepare(generated: Path) -> None:
    generated = generated.resolve(strict=True)
    client_contract = load_json(CLIENT_CONTRACT)
    server_contract = load_json(SERVER_CONTRACT)

    if client_contract.get("target") != EXPECTED_CLIENT_TARGET:
        raise ValueError(f"client target drift: {client_contract.get('target')!r}")

    server_target = dict(client_contract["target"])
    server_target.pop("geckolib")
    if server_contract.get("target") != server_target:
        raise ValueError("client/server target contracts disagree")
    if server_contract.get("geckolib", {}).get("version") != client_contract["target"]["geckolib"]:
        raise ValueError("client/server GeckoLib contracts disagree")

    connection = client_contract.get("connection")
    if connection != {
        "host": "127.0.0.1",
        "port": 25565,
        "mechanism": "ConnectScreen.startConnecting@StartupReadyScreen",
        "startupScreens": ["TitleScreen", "AccessibilityOnboardingScreen"],
    }:
        raise ValueError(f"unsupported live-client connection contract: {connection!r}")

    build_path = generated / "build.gradle"
    build = build_path.read_text(encoding="utf-8")
    client_marker = """    client {
        systemProperty 'neoforge.enabledGameTestNamespaces', project.mod_id
    }
"""
    client_replacement = """    client {
        systemProperty 'neoforge.enabledGameTestNamespaces', project.mod_id
        systemProperty 'i3golden.clientProofPath', file('run/client/client-runtime-proof.json').getAbsolutePath()
    }
"""
    if client_marker not in build:
        raise ValueError("canonical client run marker missing")
    build = build.replace(client_marker, client_replacement, 1)
    build_path.write_text(build, encoding="utf-8", newline="\n")

    main_path = generated / "src/main/java/dev/example/i3golden/I3GoldenMod.java"
    main = main_path.read_text(encoding="utf-8")
    registry_marker = "        GoldenSampleMobRegistry.register(modBus);\n"
    listener_line = (
        "        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener("
        "GoldenSampleMobClientProofServer::onPlayerLoggedIn);\n"
    )
    if registry_marker not in main:
        raise ValueError("runtime registry marker missing from generated main class")
    if listener_line not in main:
        main = main.replace(registry_marker, registry_marker + listener_line, 1)
    main_path.write_text(main, encoding="utf-8", newline="\n")

    client_main_path = generated / "src/main/java/dev/example/i3golden/client/I3GoldenModClient.java"
    client_main = client_main_path.read_text(encoding="utf-8")
    renderer_marker = "        modBus.addListener(GoldenSampleMobClient::registerRenderers);\n"
    client_listener_line = (
        "        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener("
        "GoldenSampleMobClientRuntimeProof::onClientTick);\n"
    )
    if renderer_marker not in client_main:
        raise ValueError("runtime client renderer marker missing from generated client class")
    if client_listener_line not in client_main:
        client_main = client_main.replace(renderer_marker, renderer_marker + client_listener_line, 1)
    client_main_path.write_text(client_main, encoding="utf-8", newline="\n")

    java_root = generated / "src/main/java/dev/example/i3golden"
    client_root = java_root / "client"
    shutil.copyfile(
        FIXTURES / "GoldenSampleMobClientProofServer.java",
        java_root / "GoldenSampleMobClientProofServer.java",
    )
    shutil.copyfile(
        FIXTURES / "GoldenSampleMobClientRuntimeProof.java",
        client_root / "GoldenSampleMobClientRuntimeProof.java",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare target-exact live-client GeckoLib proof fixtures.")
    parser.add_argument("generated", type=Path)
    args = parser.parse_args()
    prepare(args.generated)
