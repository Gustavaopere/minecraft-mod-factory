# Narrative golden corpus v1

Corpus sintético mínimo da Factory. Ele existe somente para testar contratos reutilizáveis e não representa lore de nenhum consumidor.

`story/` cobre um caminho positivo de inventory, knowledge/evidence, relationship/memory/autonomy e chronology/causality. `negative/` cobre diagnostics spoiler-safe com estado editorial inválido, referência global ausente e alvo de knowledge ausente.

Os arquivos em `expected/` são goldens versionados. O workflow materializa os outputs atuais em `.factory-ci/narrative-golden/` e `golden_check.py` exige igualdade byte a byte.
