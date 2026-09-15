# 17 — Golden Corpus Release and Compatibility ⬜

Status: planejado.

## Objetivo

Fechar a ferramenta narrativa como uma capability estável, testável e atualizável por consumidores sem regressões silenciosas.

## Capability pretendida

- corpus mínimo de fixtures positivas e negativas cobrindo os principais contratos;
- golden outputs para inventory e diagnostics spoiler-safe;
- política explícita de compatibilidade de profiles;
- testes de upgrade entre revisões da Factory;
- documentação de breaking changes e migrações;
- gate de release para garantir que consumidores pinados possam atualizar de forma controlada.

## Dependências

Os milestones anteriores devem ter contratos suficientemente estáveis para formar um corpus de compatibilidade representativo.

## Gate de conclusão

Suite golden reproduzível, checks de compatibilidade, documentação de upgrade e release procedure validada por pelo menos um consumidor real.