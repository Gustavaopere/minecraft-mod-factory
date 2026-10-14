# 14 — Chronology and Causality Graph Checks ✅

Status: concluído na branch de implementação; release em `main` depende do merge do PR #118.

## Objetivo

Adicionar checks estruturais de cronologia e causalidade sobre IDs estáveis sem tentar escrever a história pelo consumidor.

## Capability pretendida

- relações BEFORE/AFTER configuráveis entre eventos;
- detecção de ciclos cronológicos impossíveis quando o corpus fornecer relações explícitas;
- detecção de referências causais ausentes ou inválidas quando configuradas;
- checks de self-reference e arestas inconsistentes;
- relatórios spoiler-safe por padrão;
- nenhuma inferência de ordem temporal a partir de prosa livre.

## Dependências

- grafo estável de IDs do `validate_story.py`;
- contratos de eventos e auxiliares suficientemente definidos pelo consumidor.

## Gate de conclusão

Algoritmo determinístico coberto por testes de ciclo/ordem, documentação de limites e integração em corpus real sem inferência semântica.

## Evidência de conclusão

- algoritmo determinístico em `advanced_contracts.py`, exposto por `validate_advanced.py`;
- testes cobrem ciclos, self-reference, referências ausentes e conflitos; o golden corpus cobre BEFORE/AFTER e causalidade explícita;
- o profile real do consumidor declara o contrato `EVT`, mas o slice selecionado ainda não contém registros estáveis `EVT-####`; nenhuma aresta foi fabricada;
- consumer run `35058474136` prova que o hook é compatível com o corpus real; a semântica de grafo é comprovada pela suíte/golden Factory run `35058398971`.
