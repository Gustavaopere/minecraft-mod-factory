# 11 — Auxiliary Document Contracts 🔄

Status: em execução.

## Problema

Arquivos auxiliares como lifecycle de quest, ficha de autoria de NPC e nota de relação podem conter estrutura editorial importante sem declarar uma entidade própria no H1. Hoje eles recebem checks globais, mas não contratos estruturais específicos por tipo de documento.

## Objetivo

Adicionar `auxiliary_document_contracts` ao profile para selecionar documentos por glob relativo a `story_root` e validar seções/referências sem transformar esses arquivos em declarações de entidade.

## Escopo planejado

- seleção por glob relativo e fail-closed para path traversal;
- `required_sections` por contrato auxiliar;
- `reference_rules` opcionais por seção;
- issue codes próprios;
- nenhum ID mencionado em H1 auxiliar vira declaração;
- contratos auxiliares não se aplicam a arquivos que já são entity records;
- compatibilidade total com profiles antigos.

## Estado atual

O design foi aprovado e está versionado na branch `design/narrative-auxiliary-document-contracts`. A implementação em `profile.py`/`validate_story.py` ainda não foi concluída, portanto este milestone não recebe ✅.

## Próximo gate

TDD RED → GREEN na Factory, PR, checks completos, merge certificado e só depois pin/ativação no consumidor RPG.