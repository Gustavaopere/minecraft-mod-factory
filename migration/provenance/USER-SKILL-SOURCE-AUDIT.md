# Auditoria dos 20 pacotes de skills recebidos

Snapshot auditado em 2026-09-07.

## Classificação

**Preferred:** `minecraft-neoforge-engineering`, `minecraft-neoforge-modpack-debugging`, `minecraft-jar-reverse-engineering`, `minecraft-modpack-bisect`, `minecraft-dependency-compatibility-graph`, `modpack-inventory-redundancy-audit`.

**Overlay 1.21.1 obrigatório:** `minecraft-ci-release`, `minecraft-commands-scripting`, `minecraft-datapack`, `minecraft-imagegen`, `minecraft-modding`, `minecraft-resource-pack`, `minecraft-testing`, `minecraft-world-generation`, `minecraft-worldedit-ops`.

**Reference-only/incompleta:** `minecraft-mod-dev`. O `SKILL.md` recebido referencia `references/mod-links.md`, `references/migration-guide.md` e `scripts/mod-env-check.sh`, mas esses três arquivos não vieram no ZIP.

**Desativadas por padrão neste projeto:** `minecraft-plugin-dev`, `minecraft-server-admin`, `minecraft-essentials-ops`, `minecraft-multiloader`. Não são skills ruins; apenas não correspondem ao runtime normal do RPG Skill Tree, que é NeoForge single-loader.

## Risco de versão

A auditoria encontrou exemplos/tokens posteriores a 1.21.1 em vários pacotes, incluindo 1.21.4+, 1.21.8+, 1.21.9, 1.21.10 e 1.21.11. Por isso, os `SKILL.md` em `library/` são adaptações canônicas do propósito e workflow úteis ao projeto, não uma promoção cega de todos os exemplos dos ZIPs.

## Regra

Nenhuma skill suplanta código/JAR/build da versão alvo. Quando houver conflito, siga `VERSION-AUTHORITY.md`.
