# Narrative toolkit compatibility policy

A unidade de compatibilidade pública é `profile_contract_revision`.

## Dentro da mesma revisão

Mudanças devem ser aditivas: novas chaves opcionais, novos validators opt-in e novos issue codes para contratos recém-ativados são permitidos. Adicionar ou remover uma chave obrigatória sem alterar a revisão é breaking change e `golden_check.compatibility_issues` deve rejeitar a mudança.

Profiles que não ativam uma capability nova devem continuar carregando e mantendo o comportamento anterior.

## Mudança de revisão

Uma nova revisão é obrigatória quando a Factory altera uma exigência necessária para carregar profiles existentes ou muda um contrato de forma incompatível. O descriptor novo deve conter:

```json
{
  "profile_contract_revision": 2,
  "migration": {
    "from_revision": 1,
    "document": "narrative/migrations/profile-v1-to-v2.md"
  }
}
```

A migration deve explicar mudanças, comandos de verificação, rollback e diferenças esperadas nos goldens. A suíte testa que uma troca de revisão sem migration explícita falha.

## Pinning do consumidor

Consumidores devem pinçar um commit/tag conhecido da Factory para CI de compatibilidade. Atualizações são deliberadas: primeiro executar validators/goldens contra o commit novo; depois revisar diferenças; só então mover o pin.

Nenhum gate da Factory escreve em canon do consumidor.
