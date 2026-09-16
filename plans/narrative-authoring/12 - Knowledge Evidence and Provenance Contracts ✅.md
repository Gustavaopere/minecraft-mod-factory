# 12 — Knowledge Evidence and Provenance Contracts ✅

Status: concluído na branch de implementação; release em `main` depende do merge do PR #118.

## Objetivo

Evoluir a validação estrutural para documentos que registram conhecimento, evidência, rumor, testemunho e provenance, sem tentar decidir semanticamente se uma afirmação é verdadeira.

## Capability pretendida

- contratos opt-in para campos/seções como origem, portador do conhecimento, evidência associada, confiabilidade, limites do que é provado e perda/alteração;
- distinção estrutural entre ouvir, ver, evidenciar, participar, causar e confirmar quando o consumidor declarar esses estados;
- validação de referências estáveis exigidas por provenance;
- erros determinísticos para ausência de campos obrigatórios configurados;
- nenhuma inferência automática de verdade, canon ou legitimidade epistemológica.

## Dependências

- milestone 11 concluído para cobrir documentos auxiliares quando necessário;
- auditoria de corpus real antes de ativar regras mais restritivas.

## Gate de conclusão

Testes TDD, documentação de profile, corpus de exemplo e integração comprovada sem exigir conteúdo fabricado do consumidor.

## Evidência de conclusão

- implementação: `narrative/tooling/advanced_contracts.py` e `validate_advanced.py`;
- contrato: `narrative/PROFILE_CONTRACT.md`;
- tests/fixtures: `test_advanced_contracts.py` + `narrative/golden/v1`;
- integração real: `neoforge-rpg-skilltree` SHA `70b62951c39201f712b739d93a468bc9a0e248da`, run `35058474136` = `success`;
- Factory SHA `99292829b25025b4cb7130a05a8221e0d7a5a19e`, run `35058398971` = `success`.
