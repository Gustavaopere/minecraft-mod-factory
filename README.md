# Minecraft Mod Factory

Infraestrutura reutilizável para projetar, gerar, validar, testar e integrar mods Minecraft 1.21.1 com NeoForge e Java 21.

## Autoridade

Este repositório é a fonte de verdade da infraestrutura comum de produção de mods e assets: instruções, skills, standards, contracts, schemas, templates, validators, tooling, testes, CI, catálogos de providers e contratos de integração.

Ele não substitui os repositórios individuais dos mods. Código runtime, dados específicos, releases e decisões exclusivas de cada mod permanecem no respectivo repositório.

O repositório `Gustavaopere/neoforge-rpg-skilltree` permanece a autoridade do runtime RPG e a origem histórica da infraestrutura que está sendo migrada. A modlist física e o conteúdo específico do RPG permanecem lá.

O domínio artístico "Repo Textura" passa a existir nesta Factory, preservando formatos-fonte como `.bbmodel` e proibindo conversões silenciosas entre pipelines.

## Estado da migração

A Factory está em bootstrap e migração controlada conforme os planos canônicos V1.1 de Mod Engineering e V5.1 do pipeline artístico. Nenhum conteúdo deve ser copiado em massa sem inventário, classificação, adaptação de paths e validação.

Consulte `STATUS.md` para o boundary operacional atual e `plans/` para os planos canônicos quando materializados.
