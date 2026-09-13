# Router de skills — Minecraft Mod Factory

Leia `VERSION-AUTHORITY.md` antes de escolher uma skill quando a tarefa depender de runtime/provider. Se houver ação manual do usuário, aplique também `USER-GUIDED-WORKFLOW.md`.

## Engenharia NeoForge 1.21.1

Preferência:
1. `library/minecraft-neoforge-engineering/SKILL.md`
2. `library/minecraft-testing/SKILL.md`
3. `library/minecraft-ci-release/SKILL.md`
4. `library/minecraft-jar-reverse-engineering/SKILL.md`

Para crash/hang/load use `minecraft-neoforge-modpack-debugging`; para isolamento de interação use `minecraft-modpack-bisect`; para dependências use `minecraft-dependency-compatibility-graph`; para redundância/inventário use `modpack-inventory-redundancy-audit`.

## Arte, modelos e animação

Para asset visual project-owned:
1. `../art/VISUAL-STYLE-BIBLE.md`
2. `../art/skills/minecraft-asset-art-direction/SKILL.md`
3. `../art/templates/ASSET-BRIEF.md`, `MODEL-BRIEF.md` ou `ANIMATION-BRIEF.md`
4. `../art/skills/minecraft-blockbench-geckolib/SKILL.md`
5. `../art/tooling/blockbench/asset-toolkit/asset_toolkit.js`
6. `../art/skills/minecraft-visual-qa/SKILL.md` + `../art/standards/VISUAL-QA.md`

O domínio `art/` é authority da infraestrutura visual comum. O runtime permanece no repositório do mod.

## Autoria narrativa

Para lore, NPCs, quests, facções, locais, eventos, evidências, diálogos, relações, macroprogressão ou epílogos:
1. leia o profile/instruções do repositório consumidor;
2. use `../narrative/skills/minecraft-narrative-authoring/SKILL.md`;
3. use `../narrative/templates/` como scaffolds genéricos;
4. valide com `../narrative/tooling/validate_story.py` e `validate_dialogues.py`;
5. use `story_inventory.py` antes de criar IDs novos;
6. mantenha todo conteúdo/cânone resultante no repositório consumidor.

A Factory não substitui Campaign Bible ou outra authority de lore definida pelo projeto consumidor. O profile local define families de ID/estado/seções; o tooling não hardcodeia a campanha.

## VFX, spells e áudio

VFX geral: `../art/skills/minecraft-vfx-engineering/SKILL.md` + `../art/templates/VFX-BRIEF.md` + `../art/standards/VFX-QA.md`.
Spells/abilities: `../art/skills/minecraft-spell-production/SKILL.md`, `../art/skills/minecraft-spell-vfx-engineering/SKILL.md`, `../art/skills/minecraft-audio-design/SKILL.md`.

Provider-native vem primeiro, mas nenhum provider é assumido por nome: versão/API deve ser provada contra a instalação física.

## Material histórico não ativo

Skills históricas preservadas em `../migration/provenance/historical-skills/library/` continuam `REFERENCE_ONLY` até promoção explícita.

## QA visual

Build/editor preview não constitui PASS visual. Para afirmar que um asset está pronto, use `../art/skills/minecraft-visual-qa/SKILL.md` e evidência in-game conforme `../art/standards/VISUAL-QA.md`.
