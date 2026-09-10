# Skills e instruções especializadas — Minecraft Mod Factory

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
