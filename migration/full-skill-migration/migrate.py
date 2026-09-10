#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("full_skill_policy", HERE / "validate.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load frozen migration policy")
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)

FACTORY_REPO = "Gustavaopere/minecraft-mod-factory"
OLD_REPO = "Gustavaopere/neoforge-rpg-skilltree"

README = """# Skills e instruções especializadas — Minecraft Mod Factory

Este diretório é o ponto de entrada das skills compartilhadas usadas pela Factory. A Factory é a autoridade da infraestrutura comum; os repositórios individuais dos mods continuam sendo a autoridade de seus runtimes.

## Leia primeiro

1. `ROUTER.md` — escolhe a skill adequada e respeita as authorities de engenharia e arte.
2. `VERSION-AUTHORITY.md` — fixa Minecraft 1.21.1 / NeoForge 21.1.x / Java 21 e exige evidência da versão física exata.
3. `USER-GUIDED-WORKFLOW.md` — limita ações manuais do usuário a uma etapa verificável por vez.

## Estrutura ativa

- `library/<skill>/` — skills recebidas que foram promovidas e revalidadas para uso compartilhado;
- `../art/skills/<skill>/` — skills project-authored de arte, Blockbench, VFX, spells, áudio e QA visual;
- `../art/standards/` — contratos e checklists artísticos;
- `../art/templates/` — briefs reutilizáveis;
- `../art/tooling/blockbench/asset-toolkit/` — Minecraft Mod Factory Asset Toolkit;
- `../art/golden-samples/` — corpus `REFERENCE-ONLY`, nunca authority de runtime/API.

## Proveniência histórica

A origem histórica da frente `IMPLEMENTAR SKILL` é `Gustavaopere/neoforge-rpg-skilltree@2ecea4178aa7ac80f99955ab045e296da25376ec`. Material recebido que não foi promovido permanece preservado em `../migration/provenance/historical-skills/` e não deve ser roteado como capability ativa. Os registros dos bundles recebidos ficam em `../migration/provenance/USER-SKILL-SOURCE-MANIFEST.md`, `USER-SKILL-SOURCE-AUDIT.md` e `FULL-USER-SKILL-IMPORT.md`.

## Skills project-authored ativas

- `minecraft-asset-art-direction`
- `minecraft-blockbench-geckolib`
- `minecraft-vfx-engineering`
- `minecraft-spell-vfx-engineering`
- `minecraft-spell-production`
- `minecraft-audio-design`
- `minecraft-visual-qa`

## Skills compartilhadas recebidas e ativas

- `minecraft-neoforge-engineering`
- `minecraft-testing`
- `minecraft-ci-release`
- `minecraft-jar-reverse-engineering`
- `minecraft-dependency-compatibility-graph`
- `minecraft-modpack-bisect`
- `minecraft-neoforge-modpack-debugging`
- `modpack-inventory-redundancy-audit`

## Segurança de versão

Payloads multi-versão não são authority. Exemplos de versões posteriores, Fabric, Forge legado, Paper ou multi-loader só podem ser usados após prova explícita para o alvo físico atual. A modlist física continua externa à Factory e deve ser consultada na authority vigente antes de afirmar suporte de provider.
"""

ROUTER = """# Router de skills — Minecraft Mod Factory

Leia `VERSION-AUTHORITY.md` antes de escolher uma skill. Se houver ação manual do usuário, aplique também `USER-GUIDED-WORKFLOW.md`.

## Engenharia NeoForge 1.21.1

Preferência:
1. `library/minecraft-neoforge-engineering/SKILL.md`
2. `library/minecraft-testing/SKILL.md`
3. `library/minecraft-ci-release/SKILL.md`
4. `library/minecraft-jar-reverse-engineering/SKILL.md`

Para crash/hang/load use `minecraft-neoforge-modpack-debugging`; para isolamento de interação use `minecraft-modpack-bisect`; para dependências use `minecraft-dependency-compatibility-graph`; para redundância/inventário use `modpack-inventory-redundancy-audit`. Sempre parta de JARs, logs e modlist físicos atuais.

## Arte, modelos e animação

Para asset visual project-owned:
1. `../art/VISUAL-STYLE-BIBLE.md`
2. `../art/skills/minecraft-asset-art-direction/SKILL.md`
3. `../art/templates/ASSET-BRIEF.md`, `MODEL-BRIEF.md` ou `ANIMATION-BRIEF.md`
4. `../art/skills/minecraft-blockbench-geckolib/SKILL.md`
5. `../art/tooling/blockbench/asset-toolkit/asset_toolkit.js`
6. `../art/skills/minecraft-visual-qa/SKILL.md` + `../art/standards/VISUAL-QA.md`
7. opcionalmente `../art/golden-samples/model-asset/`, sempre `REFERENCE-ONLY`.

O domínio `art/` da Factory é a authority da infraestrutura visual comum. Um export é handoff; o runtime do mod permanece no repositório do próprio mod.

## VFX, spells e áudio

VFX geral: `../art/skills/minecraft-vfx-engineering/SKILL.md` + `../art/templates/VFX-BRIEF.md` + `../art/standards/VFX-QA.md`.

Spells/abilities: `../art/skills/minecraft-spell-production/SKILL.md`, `../art/skills/minecraft-spell-vfx-engineering/SKILL.md`, `../art/standards/SPELL-PRESENTATION-CONTRACT.md`, `../art/skills/minecraft-audio-design/SKILL.md`, `../art/templates/AUDIO-CUE-SHEET.md` e `../art/standards/AUDIO-QA.md`.

Provider-native vem primeiro, mas nenhum provider é assumido por nome: versão/API deve ser provada contra a instalação física.

## Material histórico não ativo

`minecraft-commands-scripting`, `minecraft-datapack`, `minecraft-resource-pack`, `minecraft-world-generation`, `minecraft-imagegen`, `minecraft-mod-dev`, `minecraft-modding`, `minecraft-plugin-dev`, `minecraft-server-admin`, `minecraft-essentials-ops`, `minecraft-multiloader` e `minecraft-worldedit-ops` estão preservados em `../migration/provenance/historical-skills/library/` como `REFERENCE_ONLY`. Não os carregue como authority ativa sem uma decisão posterior de promoção e nova validação de versão/escopo.

## QA visual

Build/editor preview não constitui PASS visual. Para afirmar que um asset está pronto, use `../art/skills/minecraft-visual-qa/SKILL.md` e evidência in-game conforme `../art/standards/VISUAL-QA.md`.
"""

VERSION_AUTHORITY = """# Autoridade de versão para skills e instruções

## Alvo

- Minecraft: **1.21.1**
- NeoForge: **21.1.x**
- Java: **21**

A versão exata das dependências deve vir do build, metadata, JARs e modlist física vigente do ambiente/repositório alvo.

## Ordem de autoridade

Para classe, método, evento, registry, resource path, pack format, assinatura, comportamento de provider ou compatibilidade:
1. código/build/metadata realmente presentes no repositório runtime alvo;
2. JAR/modlist física mais recente;
3. source/JAR/documentação oficial da versão exata;
4. planos, contracts e decisões canônicas da Minecraft Mod Factory;
5. skill project-authored aplicável;
6. skill compartilhada em `skills/library/`;
7. material `REFERENCE_ONLY` e exemplos de outras versões apenas como referência conceitual.

## Fail-closed

Se algo version-sensitive não puder ser confirmado para Minecraft 1.21.1 / NeoForge 21.1.x, não invente API, signature, registry, path ou comportamento. Não transplante silenciosamente exemplos de versões posteriores, Fabric, Forge legado ou Paper. Integrações opcionais permanecem indisponíveis até existir evidência suficiente.

A presença nominal de GeckoLib, Photon, AAA Particles/Effekseer ou qualquer outro provider não prova uma API específica; a versão física exata precisa ser verificada.
"""

SKILL_VALIDATOR = r'''#!/usr/bin/env python3
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
ART = REPO_ROOT / "art"
SHARED = ROOT / "library"
ART_SKILLS = ART / "skills"
ARCHIVE = REPO_ROOT / "migration" / "provenance" / "historical-skills" / "library"

EXPECTED_SHARED = {"minecraft-ci-release", "minecraft-dependency-compatibility-graph", "minecraft-jar-reverse-engineering", "minecraft-modpack-bisect", "minecraft-neoforge-engineering", "minecraft-neoforge-modpack-debugging", "minecraft-testing", "modpack-inventory-redundancy-audit"}
EXPECTED_ART = {"minecraft-asset-art-direction", "minecraft-audio-design", "minecraft-blockbench-geckolib", "minecraft-spell-production", "minecraft-spell-vfx-engineering", "minecraft-vfx-engineering", "minecraft-visual-qa"}
EXPECTED_ARCHIVE = {"minecraft-commands-scripting", "minecraft-datapack", "minecraft-essentials-ops", "minecraft-imagegen", "minecraft-mod-dev", "minecraft-modding", "minecraft-multiloader", "minecraft-plugin-dev", "minecraft-resource-pack", "minecraft-server-admin", "minecraft-world-generation", "minecraft-worldedit-ops"}

def skill_set(root):
    return {p.parent.name for p in root.glob("*/SKILL.md")}

def require_set(label, actual, expected):
    if actual != expected:
        raise SystemExit(f"{label} mismatch: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

def validate_names(root):
    for path in root.glob("*/SKILL.md"):
        match = re.search(r"^name:\s*([^\n]+)$", path.read_text(encoding="utf-8"), re.MULTILINE)
        if not match or match.group(1).strip() != path.parent.name:
            raise SystemExit(f"invalid skill name metadata: {path}")

require_set("shared active skills", skill_set(SHARED), EXPECTED_SHARED)
require_set("art active skills", skill_set(ART_SKILLS), EXPECTED_ART)
require_set("reference-only archived skills", skill_set(ARCHIVE), EXPECTED_ARCHIVE)
validate_names(SHARED)
validate_names(ART_SKILLS)

for required in [ROOT/"README.md", ROOT/"ROUTER.md", ROOT/"VERSION-AUTHORITY.md", ROOT/"USER-GUIDED-WORKFLOW.md", ART/"VISUAL-STYLE-BIBLE.md", ART/"tooling/blockbench/asset-toolkit/asset_toolkit.js", ART/"tooling/blockbench/asset-toolkit/COMPATIBILITY.md", ART/"golden-samples/validate_golden_samples.js", ART/"golden-samples/validate_reference_evidence.js"]:
    if not required.is_file():
        raise SystemExit(f"missing Factory skill/art capability: {required.relative_to(REPO_ROOT)}")

node = shutil.which("node")
if not node:
    raise SystemExit("Node.js is required to validate Factory art tooling")
toolkit = ART / "tooling/blockbench/asset-toolkit"
subprocess.run([node, "--check", str(toolkit/"asset_toolkit.js")], check=True)
for test in sorted(toolkit.rglob("*.test.js")):
    subprocess.run([node, "--test", str(test)], check=True)
subprocess.run([node, str(toolkit/"build_toolkit_bundle.js"), "--check"], check=True)
for validator in [ART/"golden-samples/validate_golden_samples.js", ART/"golden-samples/validate_reference_evidence.js"]:
    subprocess.run([node, "--check", str(validator)], check=True)
    subprocess.run([node, str(validator)], check=True)
rendered = ART/"tooling/validators/validate_golden_reference_rendered_edges.js"
subprocess.run([node, "--check", str(rendered)], check=True)
subprocess.run([node, str(rendered), "--self-test"], check=True)
subprocess.run([node, str(rendered)], check=True)
print("OK: 15 active Factory skills, 12 reference-only historical skills, neutral Asset Toolkit, standards and Golden Samples validated")
'''

COMPATIBILITY = """# Asset Toolkit legacy compatibility

M5 moved the canonical Toolkit to `art/tooling/blockbench/asset-toolkit/` and neutralized filenames and user-facing branding to **Minecraft Mod Factory Asset Toolkit**.

For legacy compatibility, the Blockbench plugin ID `rpg_asset_toolkit` and existing action IDs prefixed `rpg_asset_toolkit_` are intentionally retained. They are compatibility identifiers only; they do not make the RPG repository an authority and must not be used as new repository/path naming. Changing those IDs requires an explicit compatibility migration.

The canonical generated plugin filename is `asset_toolkit.js`. The generated bundle remains derived from modular source via `build_toolkit_bundle.js` and must never be edited by hand.
"""


def write_bytes(path: Path, data: bytes, source_mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if source_mode is not None and source_mode & 0o111:
        path.chmod(path.stat().st_mode | 0o111)


def write_text(path: Path, text: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)


def generic_adapt(relative: str, text: str) -> str:
    text = text.replace(OLD_REPO, FACTORY_REPO)
    replacements = [
        ("PROJECT-INSTRUCTIONS/skills/tools/blockbench/rpg-asset-toolkit", "art/tooling/blockbench/asset-toolkit"),
        ("PROJECT-INSTRUCTIONS/skills/golden-samples", "art/golden-samples"),
        ("PROJECT-INSTRUCTIONS/skills/standards", "art/standards"),
        ("PROJECT-INSTRUCTIONS/skills/templates", "art/templates"),
        ("../../tools/blockbench/rpg-asset-toolkit", "../../tooling/blockbench/asset-toolkit"),
        ("tools/blockbench/rpg-asset-toolkit", "art/tooling/blockbench/asset-toolkit"),
        ("RPG Asset Toolkit", "Minecraft Mod Factory Asset Toolkit"),
        ("RPG Asset MCP", "Minecraft Mod Factory Asset MCP"),
        ("rpg-asset-toolkit", "asset-toolkit"),
        ("rpg_asset_toolkit.", "asset_toolkit."),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    if relative == "scripts/validate_golden_reference_rendered_edges.js":
        text = text.replace("path.resolve(__dirname, '..', 'golden-samples')", "path.resolve(__dirname, '..', '..', 'golden-samples')")
    if relative.endswith("PROJECT-OVERLAY.md"):
        text = text.replace(
            "is the shared integration/instruction/tooling hub",
            "is the canonical common infrastructure/control-plane repository",
        )
        text = text.replace(
            "Repo Textura remains the artistic source of truth",
            "The Factory `art/` domain is the artistic source of truth for common visual/asset infrastructure",
        )
    return text


def adapted_bytes(relative: str, data: bytes) -> bytes:
    if relative == "README.md":
        return README.encode("utf-8")
    if relative == "ROUTER.md":
        return ROUTER.encode("utf-8")
    if relative == "VERSION-AUTHORITY.md":
        return VERSION_AUTHORITY.encode("utf-8")
    if relative == "scripts/validate_skill_repository.py":
        return SKILL_VALIDATOR.encode("utf-8")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"adapted source must be UTF-8 text: {relative}") from exc
    return (generic_adapt(relative, text).rstrip() + "\n").encode("utf-8")


def materialize(source_root: Path, factory_root: Path) -> int:
    inventory, errors = POLICY.source_inventory(source_root)
    if errors:
        raise RuntimeError("; ".join(errors))
    entries = []
    for relative in sorted(inventory):
        mapping = POLICY.expected_mapping(relative)
        if mapping is None:
            raise RuntimeError(f"unmapped source: {relative}")
        destination, classification, mode = mapping
        source = source_root / relative
        target = factory_root / destination
        entries.append({
            "source_path": relative,
            "source_blob_sha": inventory[relative],
            "classification": classification,
            "destination": destination,
            "materialization_mode": mode,
        })
        if mode == "PREEXISTING_RECONCILED":
            if not target.is_file():
                raise RuntimeError(f"preexisting reconciled destination missing: {destination}")
            continue
        data = source.read_bytes()
        if mode == "SOURCE_EXACT":
            write_bytes(target, data, source.stat().st_mode)
        elif mode == "ADAPTED":
            write_bytes(target, adapted_bytes(relative, data), source.stat().st_mode)
        else:
            raise RuntimeError(f"unsupported materialization mode {mode}: {relative}")

    write_text(factory_root / "art/tooling/blockbench/asset-toolkit/COMPATIBILITY.md", COMPATIBILITY)
    manifest = {
        "schema_version": 1,
        "source_repository": POLICY.SOURCE_REPOSITORY,
        "source_revision": POLICY.SOURCE_REVISION,
        "entries": entries,
    }
    manifest_path = factory_root / POLICY.MANIFEST_REL
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"materialized {len(entries)} frozen historical skill blobs")
    return len(entries)


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize the frozen IMPLEMENTAR SKILL migration into the Factory")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--factory-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    materialize(args.source_root.resolve(), args.factory_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
