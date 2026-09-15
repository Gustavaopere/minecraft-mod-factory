# 04 — Profile Contract ✅

Status: concluído.

## Objetivo

Permitir que cada campanha configure a capability da Factory sem hardcode de IDs, paths ou regras editoriais específicas no repositório reutilizável.

## Entregue

- `story_root` e `dialogue_root` configuráveis;
- famílias de IDs em `entity_types`;
- estados editoriais e headings aceitos;
- tipo e seções obrigatórias de diálogo;
- contratos opcionais de seções por entidade;
- contratos opcionais de referências tipadas por entidade e diálogo;
- validação de configuração inválida antes do processamento do corpus.

## Evidência

- `narrative/tooling/profile.py`;
- `narrative/profiles/example.json`;
- testes em `narrative/tests/`.

## Gate de conclusão

Concluído porque consumidores podem definir políticas próprias por profile sem modificar o código da Factory.