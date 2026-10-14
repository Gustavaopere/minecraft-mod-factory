# 11 — Auxiliary Document Contracts ✅

Status: concluído na implementação da Factory; integração específica de consumidores continua separada.

## Problema resolvido

Arquivos auxiliares como lifecycle de quest, ficha de autoria de NPC e nota de relação podem conter estrutura editorial importante sem declarar uma entidade própria no H1. Antes deste milestone eles recebiam checks globais, mas não contratos estruturais específicos por tipo de documento.

## Entregue

- `auxiliary_document_contracts` opt-in no profile;
- seleção por globs relativos a `story_root`, com `**` recursivo;
- rejeição de patterns absolutos, separadores incompatíveis e segmentos `..`;
- fail-closed quando um match resolve fora de `story_root`;
- `required_sections` com aliases case-insensitive e exigência de conteúdo não vazio;
- `reference_rules` opcionais com `allowed_types` e `min_references` por IDs distintos;
- supressão de erro duplicado de referência quando a seção está ausente/vazia;
- issue codes auxiliares próprios e fatais;
- identidade preservada: H1 auxiliar não declara ID, e entity record verdadeiro tem precedência mesmo quando seu caminho casa com o glob;
- compatibilidade com profiles antigos que omitem a capability;
- cobertura TDD dedicada em `narrative/tests/test_auxiliary_document_contracts.py`.

## Evidência

- design: `docs/superpowers/specs/2026-09-15-narrative-auxiliary-document-contracts-design.md`;
- plano de implementação: `docs/superpowers/plans/2026-09-15-narrative-auxiliary-document-contracts.md`;
- produção: `narrative/tooling/profile.py` e `narrative/tooling/validate_story.py`;
- documentação/profile exemplo: `narrative/README.md` e `narrative/profiles/example.json`;
- TDD RED observado na PR #117 antes da implementação;
- GREEN do workflow `Narrative Authoring Toolkit` observado após a implementação.

## Limites

A capability valida estrutura e referências estáveis. Ela não conclui verdade/cânone, causalidade, legitimidade de conhecimento, coerência narrativa, significado de relação nem mecânicas reais de mods/providers.

## Próximo gate de consumo

Depois do merge e da certificação pós-merge da Factory, o RPG pode atualizar o SHA pinado e ativar um contrato real para seus arquivos `QST-*-lifecycle.md`. Fichas de autoria de NPC e notas de relação devem receber contratos somente após auditoria de invariantes do corpus correspondente.
