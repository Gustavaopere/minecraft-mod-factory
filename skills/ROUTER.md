# Router de skills — Minecraft Mod Factory

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
