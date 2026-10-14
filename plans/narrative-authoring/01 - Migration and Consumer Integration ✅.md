# 01 — Migration and Consumer Integration ✅

Status: concluído.

## Objetivo

Mover capability reutilizável de autoria narrativa para a Factory sem mover a campanha específica do consumidor.

## Entregue

- tooling e templates genéricos centralizados na Factory;
- profile específico mantido no repositório consumidor;
- CI do consumidor configurado para executar a Factory em revisão pinada por SHA;
- remoção da necessidade de duplicar validators/templates no projeto consumidor;
- integração validada no `neoforge-rpg-skilltree`.

## Evidência

- `plans/2026-09-13-narrative-authoring-migration.md`;
- PR #111 na Factory;
- integração posterior no consumidor por workflow pinado.

## Gate de conclusão

Concluído quando a Factory passou a ser a origem reutilizável da capability e o RPG passou a consumi-la sem transferir canon ou conteúdo de campanha para este repositório.