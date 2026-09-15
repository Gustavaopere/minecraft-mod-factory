# 05 — Story Validator ✅

Status: concluído.

## Objetivo

Validar estruturalmente o corpus narrativo e o grafo de IDs sem decidir verdade, canon ou qualidade literária.

## Entregue

- varredura de Markdown sob `story_root`;
- detecção de declarações estáveis por H1;
- checagem de duplicidade e referências;
- estados editoriais configuráveis;
- modo spoiler-safe por padrão;
- `--reveal` para revisão deliberada;
- `--strict-references` para promover referências não resolvidas a falha de CLI;
- extensão posterior para seções obrigatórias e referências tipadas.

## Evidência

- `narrative/tooling/validate_story.py`;
- suíte correspondente em `narrative/tests/`.

## Gate de conclusão

Concluído porque o validator base está em `main`, testado e utilizado por consumidor real.