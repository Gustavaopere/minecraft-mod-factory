# 15 — External Authority Reconciliation Hooks ⬜

Status: planejado.

## Objetivo

Criar pontos de integração genéricos para comparar/reconciliar narrativa versionada com uma authority externa estruturada sem acoplar a Factory a uma campanha ou serviço específico.

## Capability pretendida

- contratos de crosswalk por stable ID;
- import/export intermediário em formato neutro quando aplicável;
- provenance de origem e timestamp/revision da authority externa;
- detecção de divergência estrutural entre registros conhecidos;
- fail-closed quando a fonte exigida não estiver disponível;
- nenhuma sincronização bidirecional cega;
- adapters específicos ficam fora do core ou em camadas claramente isoladas.

## Uso esperado

Consumidores podem ligar a capability a Campaign Bible, banco narrativo ou outro sistema estruturado sem colocar conteúdo específico dentro da Factory.

## Gate de conclusão

Contrato neutro documentado, adapter de referência gratuito/local ou mockado, testes de divergência e round-trip sem sobrescrever canon automaticamente.