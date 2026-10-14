# 15 — External Authority Reconciliation Hooks ✅

Status: concluído na branch de implementação; release em `main` depende do merge do PR #118.

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

## Evidência de conclusão

- `authority_reconcile.py` implementa snapshot schema 1 com provenance, export, compare e `--required-external` fail-closed;
- `test_authority_reconcile.py` cobre round-trip/divergência/ausência da authority;
- o workflow consumidor exportou inventory real e o comparou pelo formato neutro sem escrita de volta; run `35058474136` = `success`;
- não houve consulta live ao Grimoire/TTRPG.bot nesta execução porque não havia conector Grimoire disponível. O milestone conclui o hook genérico e a prova GitHub; não afirma sync live com Grimoire.
