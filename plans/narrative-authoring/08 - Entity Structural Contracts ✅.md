# 08 — Entity Structural Contracts ✅

Status: concluído.

## Objetivo

Permitir que consumidores exijam seções estruturais específicas para famílias de entidades sem hardcode na Factory.

## Entregue

- `entity_required_sections` no profile;
- aliases de heading por chave lógica;
- validação de seção ausente;
- validação de seção vazia;
- aplicação apenas a arquivos que realmente declaram entidade no H1;
- preservação da natureza puramente estrutural do validator.

## Evidência

- PR #114;
- `narrative/tooling/profile.py`;
- `narrative/tooling/validate_story.py`;
- documentação em `narrative/README.md`.

## Gate de conclusão

Concluído porque a capability está em `main`, coberta por testes e já foi consumida por campanha real.