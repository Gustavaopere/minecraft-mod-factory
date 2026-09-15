# 09 — Dialogue Typed Reference Rules ✅

Status: concluído.

## Objetivo

Permitir que seções de diálogo imponham famílias de IDs permitidas e cardinalidade mínima de referências estáveis.

## Entregue

- `dialogue_reference_rules` no profile;
- `allowed_types` por seção;
- `min_references` com contagem de IDs distintos;
- validação contra famílias declaradas em `entity_types`;
- supressão de erros redundantes quando a seção obrigatória já está ausente/vazia;
- manutenção da resolução global de IDs fora da semântica local da seção.

## Evidência

- PR #113;
- `narrative/tooling/profile.py`;
- `narrative/tooling/validate_dialogues.py`;
- documentação e testes na `main`.

## Gate de conclusão

Concluído porque a capability está integrada, testada e disponível a qualquer profile consumidor.