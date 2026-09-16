# 13 — Relationships Memory and Autonomy Contracts ✅

Status: concluído na branch de implementação; release em `main` depende do merge do PR #118.

## Objetivo

Dar suporte estrutural mais forte a relações entre atores, memórias persistentes, dívidas/favores/grievances e autonomia de NPCs sem transformar relações em um único score.

## Capability pretendida

- contratos opt-in para dimensões de relação definidas pelo consumidor;
- referências estáveis entre ator-origem, ator-alvo, evento/memória e causa;
- estrutura para grievance, favor, debt e disponibilidade/autonomia;
- validação de que memórias relacionais apontam para eventos ou fatos estáveis quando o profile exigir;
- suporte a documentos auxiliares de relação sem criar nova família de entidade por obrigação;
- nenhum julgamento automático de afinidade, moralidade ou intenção.

## Dependências

- milestone 11 para contratos auxiliares;
- milestone 12 quando relações dependam de conhecimento/provenance.

## Gate de conclusão

TDD, documentação, fixtures positivas/negativas e integração em corpus real sem reduzir relações multidimensionais a um valor único.

## Evidência de conclusão

- implementação: `advanced_contracts.py`/`validate_advanced.py`;
- tests positivos/negativos: `test_advanced_contracts.py` e golden corpus v1;
- o profile consumidor exercita `NPC-0001-aren.md` e suas relações sistêmicas sem gerar score agregado;
- consumer run `35058474136` e Factory run `35058398971`, ambos `success`.
