# Minecraft Mod Factory

Infraestrutura reutilizável para projetar, gerar, validar, testar e integrar mods Minecraft 1.21.1 com NeoForge e Java 21.

## Autoridade

Este repositório é a fonte de verdade da infraestrutura comum de produção de mods e assets: instruções, skills, standards, contracts, schemas, templates, validators, tooling, testes, CI, catálogos de providers, contratos de integração e autoria narrativa reutilizável.

Ele não substitui os repositórios individuais dos mods. Código runtime, dados específicos, releases, decisões exclusivas de cada mod e conteúdo/cânone de campanhas permanecem no respectivo repositório consumidor.

O repositório `Gustavaopere/neoforge-rpg-skilltree` permanece a autoridade do runtime RPG e guarda o conteúdo versionado da campanha. A Factory fornece a capability reutilizável para criar, validar e organizar esse conteúdo; ela não vira Campaign Bible.

O domínio artístico "Repo Textura" passa a existir nesta Factory, preservando formatos-fonte como `.bbmodel` e proibindo conversões silenciosas entre pipelines.

## Domínios reutilizáveis

- `engineering/` — infraestrutura compartilhada de engenharia e integração;
- `art/` — direção de arte, Blockbench, assets, VFX, áudio e QA visual;
- `construction/` — capability compartilhada de construção/estrutura;
- `narrative/` — autoria narrativa reutilizável: skill, profiles, templates, validators, inventory e testes.

## Estado da migração

A Factory está em bootstrap e migração controlada conforme os planos canônicos V1.1 de Mod Engineering, V5.1 do pipeline artístico e os planos de capabilities adicionais materializados em `plans/`. Nenhum conteúdo deve ser copiado em massa sem inventário, classificação, adaptação de paths e validação.

Capability reutilizável pertence à Factory; runtime, dados, configuração e cânone específicos permanecem no repositório consumidor.

Consulte `STATUS.md`, `skills/ROUTER.md` e `plans/` para o boundary operacional atual.
