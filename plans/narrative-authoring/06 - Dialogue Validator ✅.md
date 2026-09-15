# 06 — Dialogue Validator ✅

Status: concluído.

## Objetivo

Validar arquivos de diálogo de forma independente do restante do corpus, respeitando aliases e regras definidas pelo consumidor.

## Entregue

- detecção do tipo de diálogo configurado;
- seções obrigatórias configuráveis;
- validação de headings e conteúdo não vazio;
- modo spoiler-safe;
- regras tipadas de referência por seção;
- cardinalidade mínima por referências estáveis distintas.

## Evidência

- `narrative/tooling/validate_dialogues.py`;
- `narrative/tests/`;
- extensão de referências tipadas consolidada pela PR #113.

## Gate de conclusão

Concluído porque o validator de diálogos está na `main` e suporta o contrato configurável usado pelos consumidores.