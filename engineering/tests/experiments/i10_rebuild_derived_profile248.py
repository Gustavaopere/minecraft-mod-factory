#!/usr/bin/env python3
"""Rebuild the 2026-10-14 I10 physical 21.1.248 handoff byte-for-byte.

Input: GitHub artifact 11930861353, run 38641158897, source HEAD 9403327a.
No runtime Java/source/asset rewrites, no silent profile switch, no preexisting output.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

EXPECTED_SOURCE_SHA = "e829031f60dacf8e86f70c1b46910c607fb0676b0cf437e9a7cd517e5be327d2"
EXPECTED_DERIVED_SHA = "b01a2f74218c5a14a502343145ec36380051221f2c482a2c6c29563636b7454a"
EXPECTED_COMMIT = "9403327ad50227251d8fb1f866077d16f1f3cd4b"
MODLIST_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
PROFILE = "21.1.248"


class ProfileBlocked(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact(source: str, original: str, replacement: str, label: str) -> str:
    if source.count(original) != 1:
        raise ProfileBlocked(f"{label}: expected exactly one {original!r}")
    return source.replace(original, replacement, 1)


def safely_read(directory: Path) -> dict[str, bytes]:
    root = directory.resolve(strict=True)
    if not root.is_dir() or directory.is_symlink():
        raise ProfileBlocked("source must be an existing non-symlink directory")
    files: dict[str, bytes] = {}
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ProfileBlocked(f"symlink not allowed: {item}")
        if not item.is_file():
            continue
        relative = item.relative_to(root).as_posix()
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or relative in files:
            raise ProfileBlocked(f"unsafe source member {relative}")
        files[relative] = item.read_bytes()
    if len(files) != 46:
        raise ProfileBlocked(f"expected 46 exact-source artifact files, found {len(files)}")
    if files.get("I10-SOURCE-COMMIT.txt", b"").decode().strip() != EXPECTED_COMMIT:
        raise ProfileBlocked("source commit mismatch")
    if sum(name.endswith(".java") for name in files) != 15:
        raise ProfileBlocked("source Java inventory mismatch")
    if any(name.startswith("build/") or name.startswith("run/") for name in files):
        raise ProfileBlocked("build and world files prohibited from input")
    return files


def build(files: dict[str, bytes]) -> dict[str, bytes]:
    originals = {name: sha(data) for name, data in files.items()}
    result = dict(files)
    result["gradle.properties"] = exact(
        result["gradle.properties"].decode(), "neo_version=21.1.250",
        "neo_version=21.1.248", "gradle.properties").encode()
    locks = result["gradle.lockfile"].decode()
    for original, target in (
        ("net.neoforged.fancymodloader:earlydisplay:4.0.44=",
         "net.neoforged.fancymodloader:earlydisplay:4.0.43="),
        ("net.neoforged.fancymodloader:loader:4.0.44=",
         "net.neoforged.fancymodloader:loader:4.0.43="),
        ("net.neoforged:neoforge:21.1.250=sdk,testSdk",
         "net.neoforged:neoforge:21.1.248=sdk,testSdk"),
        ("ng_dummy_ng.net.neoforged:neoforge:21.1.250=",
         "ng_dummy_ng.net.neoforged:neoforge:21.1.248="),
    ):
        locks = exact(locks, original, target, "gradle.lockfile")
    if "21.1.250" in locks or "4.0.44" in locks:
        raise ProfileBlocked("lockfile still mentions the previous loader")
    result["gradle.lockfile"] = locks.encode()
    runner = exact(result["run-i10-manual-process.py"].decode(),
                   '    "neoforge": "21.1.250",',
                   '    "neoforge": "21.1.248",', "manual process target")
    ast.parse(runner, filename="run-i10-manual-process.py")
    result["run-i10-manual-process.py"] = runner.encode()
    notice = """I10 — PERFIL FÍSICO DERIVADO PARA NEOFORGE 21.1.248

ORIGEM: artifact I10 da PR #106, commit 9403327ad50227251d8fb1f866077d16f1f3cd4b.
DESTINO: Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21.
MODLIST: SHA-256 7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00.

Este ZIP foi TRANSFORMADO DE FORMA EXPLÍCITA a partir do handoff validado em 21.1.250.
Somente os perfis/lockfile Gradle e o campo TARGET de metadados do runner foram
modificados. Os arquivos Java, modelos, recursos, scripts BAT/SH e protocolos originais
permaneceram byte a byte iguais. Veja I10-PROFILE-RECONCILIATION.json.

IMPORTANTE: ESTE PERFIL DERIVADO AINDA NÃO FOI SUBMETIDO INDEPENDENTEMENTE AO BUILD
OU À CAMPANHA FÍSICA DE DOIS CLIENTES. Os experimentos E3/E4 executaram uma fixture
instrumentada de I10 em 21.1.248, mas isso não certifica este ZIP.

Não misture este projeto isolado com a instalação existente do modpack.
Extraia em diretório NOVO e vazio. Execute o Gradle/servidor apenas depois de validar
as precondições de runtime, Python, Java 21 e acesso às dependências. Para o ambiente
de dois clientes locais, limite a porta 25565 à própria máquina (não exponha o
servidor de testes em rede pública: o helper usa online-mode=false).

O protocolo físico canônico está em:
https://github.com/Gustavaopere/minecraft-mod-factory/blob/9403327ad50227251d8fb1f866077d16f1f3cd4b/engineering/tests/i10-multiplayer-acceptance.md

O código de runtime canônico não foi editado. Os 3 P2 seguem abertos.
ESTADO: DERIVED_PROFILE_PREPARED / PHYSICAL_ACCEPTANCE_PENDING / MERGE_BLOCKED.
"""
    result["LEIA-PRIMEIRO-PERFIL-21.1.248.txt"] = notice.encode()
    changed = sorted(name for name in files if sha(result[name]) != originals[name])
    if changed != sorted(["gradle.lockfile", "gradle.properties", "run-i10-manual-process.py"]):
        raise ProfileBlocked(f"unexpected modifications: {changed}")
    manifest = {
        "schema_version": 1,
        "type": "EXPLICIT_EXPERIMENTAL_PROFILE_RECONCILIATION_NOT_A_RUNTIME_PASS",
        "source_archive": "i10-physical-handoff-9403327a.zip",
        "source_archive_sha256": EXPECTED_SOURCE_SHA,
        "source_commit": EXPECTED_COMMIT,
        "minecraft_version": "1.21.1",
        "source_neoforge": "21.1.250",
        "target_neoforge": PROFILE,
        "target_fml": "4.0.43",
        "java_version": 21,
        "physical_modlist_sha256": MODLIST_SHA,
        "conversion_contract": "Reuse exactly the 4 anchored Gradle/FML substitutions supported by the Factory I3 scaffolder, plus one TARGET field substitution in the physical helper.",
        "modified_file_sha256": {name: {"source": originals[name], "derived": sha(result[name])} for name in changed},
        "source_code_and_assets_preserved": all(
            result[name] and sha(result[name]) == originals[name]
            for name in files if name not in changed
        ),
        "modified_paths": changed,
        "new_paths": ["LEIA-PRIMEIRO-PERFIL-21.1.248.txt", "I10-PROFILE-RECONCILIATION.json"],
        "build_and_game_tests_for_this_derived_zip": "NOT_RUN",
        "prior_experiments_21_1_248": "E3/E4 used other disposable generated fixtures with read-only instrumentation; not proof for this derived ZIP.",
        "physical_two_client_acceptance": "PENDING",
        "physical_missing_neighbor_recovery": "UNREPRODUCED",
        "open_p2_threads": 3,
        "merge": "BLOCKED",
        "all_file_sha256": {name: sha(result[name]) for name in sorted(result)},
    }
    if not manifest["source_code_and_assets_preserved"]:
        raise ProfileBlocked("source or asset mutated")
    result["I10-PROFILE-RECONCILIATION.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    if len(result) != 48:
        raise ProfileBlocked("derived file inventory not equal 48")
    return result


def package(files: dict[str, bytes], destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise ProfileBlocked("refusing to overwrite evidence package")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    if sha(destination.read_bytes()) != EXPECTED_DERIVED_SHA:
        raise ProfileBlocked("DERIVED BYTE-FOR-BYTE SHA MISMATCH: stop without using output")
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ProfileBlocked("ZIP CRC failed")


def materialize(files: dict[str, bytes], target: Path) -> None:
    if target.exists() or target.is_symlink():
        raise ProfileBlocked("refusing overwrite of derived project")
    for name, data in files.items():
        dest = target.joinpath(*PurePosixPath(name).parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    assert (target / "gradle.properties").is_file()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    args = parser.parse_args()
    files = build(safely_read(args.source_dir))
    package(files, args.output_zip)
    materialize(files, args.project_dir)
    print(json.dumps({
        "verdict": "BYTE_IDENTICAL_TO_USER_DERIVED_ZIP_NOT_YET_BUILT",
        "zip_sha256": EXPECTED_DERIVED_SHA,
        "source_commit": EXPECTED_COMMIT,
        "neoforge": PROFILE,
        "files": len(files),
        "java_preserved": sum(name.endswith(".java") for name in files),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
