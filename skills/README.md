# Skills e instruções especializadas — Minecraft Mod Factory

Este diretório é o ponto de entrada das skills compartilhadas usadas pela Factory. A Factory é a autoridade da infraestrutura comum; os repositórios individuais dos mods continuam sendo a autoridade de seus runtimes e conteúdo específico.

## Leia primeiro

1. `ROUTER.md` — escolhe a skill adequada e respeita as authorities de engenharia, arte e narrativa.
2. `VERSION-AUTHORITY.md` — fixa Minecraft 1.21.1 / NeoForge 21.1.x / Java 21 e exige evidência da versão física exata quando a tarefa depende de runtime/provider.
3. `USER-GUIDED-WORKFLOW.md` — limita ações manuais do usuário a uma etapa verificável por vez.

## Estrutura ativa

- `library/<skill>/` — skills recebidas promovidas/revalidadas para uso compartilhado;
- `../art/skills/<skill>/` — skills project-authored de arte, Blockbench, VFX, spells, áudio e QA visual;
- `../narrative/skills/<skill>/` — skills project-authored de autoria narrativa reutilizável;
- `../narrative/templates/` — scaffolds narrativos genéricos;
- `../narrative/tooling/` — validators e inventory profile-driven;
- `../art/standards/`, `../art/templates/`, `../art/tooling/` — contratos e tooling artístico;
- `../art/golden-samples/` — corpus `REFERENCE-ONLY`, nunca authority de runtime/API.

## Skills project-authored ativas

- `minecraft-asset-art-direction`
- `minecraft-blockbench-geckolib`
- `minecraft-vfx-engineering`
- `minecraft-spell-vfx-engineering`
- `minecraft-spell-production`
- `minecraft-audio-design`
- `minecraft-visual-qa`
- `minecraft-narrative-authoring`

## Skills compartilhadas recebidas e ativas

- `minecraft-neoforge-engineering`
- `minecraft-testing`
- `minecraft-ci-release`
- `minecraft-jar-reverse-engineering`
- `minecraft-dependency-compatibility-graph`
- `minecraft-modpack-bisect`
- `minecraft-neoforge-modpack-debugging`
- `modpack-inventory-redundancy-audit`

## Segurança de authority

Tooling genérico não pode assumir Campaign Bible, taxonomia de IDs, estados editoriais, provider ou runtime de um projeto consumidor. Essas decisões entram por profile/instruções locais. Payloads multi-versão também não são authority de runtime.
