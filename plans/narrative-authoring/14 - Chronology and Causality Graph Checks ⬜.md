# 14 — Chronology and Causality Graph Checks ⬜

Status: planejado.

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