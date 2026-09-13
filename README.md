# Minecraft Mod Factory

Infraestrutura reutilizável para projetar, gerar, validar, testar e integrar mods Minecraft 1.21.1 com NeoForge e Java 21.

## Autoridade

Este repositório é a fonte de verdade da infraestrutura comum de produção: instruções, skills, standards, contracts, schemas, templates, validators, tooling, testes, CI, catálogos de providers, pipeline visual e tooling de autoria narrativa reutilizável.

Ele não substitui os repositórios individuais dos mods. Código runtime, dados específicos, releases, decisões exclusivas de cada mod e conteúdo/cânone de campanhas permanecem no respectivo repositório consumidor.

O repositório `Gustavaopere/neoforge-rpg-skilltree` permanece a autoridade do runtime RPG e guarda o conteúdo versionado da campanha. A Factory fornece a ferramenta para criar/validar esse conteúdo; não vira Campaign Bible.

## Domínios reutilizáveis

- `engineering/` — infraestrutura compartilhada de engenharia e integração;
- `art/` — direção de arte, Blockbench, assets, VFX, áudio e QA visual;
- `construction/` — capability compartilhada de construção/estrutura;
- `narrative/` — autoria narrativa reutilizável: skill, profiles, templates, validators, inventory e CI.

## Estado da migração

A Factory é expandida por migrações controladas. Conteúdo deve ser classificado por ownership antes de mover: capability reutilizável vem para a Factory; runtime/dados/cânone específicos permanecem no repositório consumidor.

Consulte `STATUS.md`, `skills/ROUTER.md` e os planos ativos em `plans/`.
