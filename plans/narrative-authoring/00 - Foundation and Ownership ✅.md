# 00 — Foundation and Ownership ✅

Status: concluído.

## Objetivo

Estabelecer `narrative/` como domínio reutilizável da Minecraft Mod Factory e separar claramente ferramenta de autoria de conteúdo de campanha.

## Entregue

- domínio `narrative/` na Factory;
- ownership explícito: Factory mantém skill, tooling, templates genéricos, contratos de profile e testes;
- repositórios consumidores mantêm canon/lore, NPCs, quests, facções, locais, evidências, diálogos e regras específicas;
- política de não transformar a Factory em Campaign Bible;
- operação sem dependência paga obrigatória.

## Evidência

- `narrative/README.md`;
- migração inicial consolidada pela PR #111;
- `plans/2026-09-13-narrative-authoring-migration.md`.

## Gate de conclusão

Concluído porque a fronteira de ownership e a estrutura reutilizável estão presentes na `main` e são consumidas por projeto externo.