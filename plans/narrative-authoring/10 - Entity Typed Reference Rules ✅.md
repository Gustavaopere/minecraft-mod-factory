# 10 — Entity Typed Reference Rules ✅

Status: concluído.

## Objetivo

Permitir regras tipadas de referências dentro de seções estruturais de entidades.

## Entregue

- `entity_reference_rules` no profile;
- vínculo obrigatório com chaves já declaradas em `entity_required_sections`;
- `allowed_types` por seção;
- `min_references` por IDs distintos;
- erros específicos para tipo inválido e cardinalidade insuficiente;
- ausência de inferência semântica sobre autoria, causalidade, conhecimento ou veracidade.

## Evidência

- PR #115;
- `narrative/tooling/profile.py`;
- `narrative/tooling/validate_story.py`;
- documentação e testes na `main`.

## Gate de conclusão

Concluído porque a PR #115 foi integrada e o merge `bfdc3103c7fb1ba7032646acda0509eb53e750be` foi certificado pelos checks pós-merge.