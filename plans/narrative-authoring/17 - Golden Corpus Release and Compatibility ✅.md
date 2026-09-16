# 17 — Golden Corpus Release and Compatibility ✅

Status: concluído na branch de implementação; release em `main` depende do merge do PR #118.

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

## Evidência de conclusão

- corpus/goldens: `narrative/golden/v1`;
- compatibilidade: `narrative/compat/profile-contract-v1.json` e `COMPATIBILITY.md`;
- procedimento: `narrative/RELEASE.md`;
- Factory SHA `99292829b25025b4cb7130a05a8221e0d7a5a19e`, run `35058398971` = `success`;
- consumidor real `Gustavaopere/neoforge-rpg-skilltree` SHA `70b62951c39201f712b739d93a468bc9a0e248da`, PR #578, run `35058474136` = `success`, pinado exatamente no SHA funcional da Factory;
- registro consolidado: `narrative/releases/2026-09-16-profile-v1.md`.
