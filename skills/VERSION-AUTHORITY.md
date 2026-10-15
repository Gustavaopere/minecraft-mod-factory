# Autoridade de versão para skills e instruções

## Alvo

- Minecraft: **1.21.1**
- NeoForge: **21.1.x estável mais recente compatível com Minecraft 1.21.1**
- Java: **21**

A versão estável mais recente do NeoForge compatível com Minecraft 1.21.1 deve ser resolvida no início de cada ciclo relevante de implementação ou validação. Depois de resolvida, a versão exata deve ser fixada no build, metadata, fixtures, CI e evidências daquele ciclo para garantir reprodutibilidade. Não atualizar silenciosamente o NeoForge no meio de um gate já iniciado.

A resolução exata do ciclo I10 atual é NeoForge **21.1.250**. Esse valor é evidência reproduzível deste ciclo, não um alvo permanente para ciclos futuros.

A modlist física vigente continua sendo autoridade para o que está efetivamente instalado no ambiente. Ela não congela permanentemente o alvo de futuros ciclos: se uma versão estável 21.1.x mais recente e compatível existir no início do próximo ciclo, o alvo deve ser resolvido novamente e as APIs, build e integrações relevantes devem ser revalidados.

## Ordem de autoridade

Para classe, método, evento, registry, resource path, pack format, assinatura, comportamento de provider ou compatibilidade:
1. código/build/metadata realmente presentes no repositório runtime alvo;
2. versão exata do NeoForge resolvida e fixada para o ciclo, incluindo source/JAR oficial correspondente;
3. JAR/modlist física mais recente do ambiente;
4. documentação oficial da versão exata;
5. planos, contracts e decisões canônicas da Minecraft Mod Factory;
6. skill project-authored aplicável;
7. skill compartilhada em `skills/library/`;
8. material `REFERENCE_ONLY` e exemplos de outras versões apenas como referência conceitual.

## Fail-closed

Se algo version-sensitive não puder ser confirmado para Minecraft 1.21.1 / Java 21 / versão estável NeoForge 21.1.x exata resolvida para o ciclo, não invente API, signature, registry, path ou comportamento. Não transplante silenciosamente exemplos de versões posteriores, Fabric, Forge legado ou Paper. Integrações opcionais permanecem indisponíveis até existir evidência suficiente.

A presença nominal de GeckoLib, Photon, AAA Particles/Effekseer ou qualquer outro provider não prova uma API específica; a versão física exata precisa ser verificada.
