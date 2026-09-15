# 12 — Knowledge Evidence and Provenance Contracts ⬜

Status: planejado.

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