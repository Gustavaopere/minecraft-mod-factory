# Autoridade de versão para skills e instruções

## Alvo físico atual

- Minecraft: **1.21.1**
- NeoForge: **21.1.248**
- Java: **21**

A versão exata de Gradle, NeoGradle/UserDev, mappings e dependências de um mod deve ser lida do runtime repository ou de um template Factory já validado. Não copie configuração do RPG por analogia.

## Ordem de autoridade

Para classe, método, evento, registry, resource path, pack format, assinatura, comportamento de provider ou compatibilidade:

1. código/build/metadata no runtime authority repository alvo;
2. JAR e modlist física mais recente;
3. source/JAR/documentação oficial da versão exata;
4. contratos e decisões canônicas da Factory;
5. skill específica já migrada e validada;
6. exemplos de outras versões apenas como referência conceitual.

## Fail-closed

Se algo version-sensitive não puder ser confirmado para Minecraft 1.21.1 / NeoForge 21.1.248, não invente API, signature, registry, path, capability ou compatibilidade. Registre a pendência e mantenha a integração indisponível/fail-closed quando necessário.

Presença na modlist física prova presença/versão, não prova uma API, runtime health ou autorização do pipeline.
