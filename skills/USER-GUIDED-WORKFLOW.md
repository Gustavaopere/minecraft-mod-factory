# Protocolo obrigatório para etapas manuais com o usuário

Quando o trabalho exigir uma ação que o agente não consegue executar diretamente, forneça **uma única etapa operacional por vez**, peça a evidência necessária e pare antes da próxima ação manual.

## Regras

1. Uma etapa manual deve ter um objetivo verificável.
2. Agrupe apenas cliques inseparáveis que formam a mesma ação atômica.
3. Interface gráfica: peça screenshot quando o estado visual for a melhor evidência.
4. Terminal: normalmente um comando por vez quando a saída decide o próximo passo.
5. Não presuma que instalação, build, export, import, login, configuração ou teste funcionou.
6. Se a evidência não confirmar o resultado, corrija a etapa atual antes de avançar.
7. Se o agente possuir ferramenta autorizada capaz de executar a ação com segurança, execute diretamente em vez de transferir trabalho ao usuário.
8. Antes de ação destrutiva ou difícil de reverter, verifique backup, branch, checkpoint ou cópia apropriada.
9. Não mande o usuário executar antecipadamente ações futuras para adiantar.
10. Pode explicar o panorama geral, mas não transformar o panorama em uma longa lista de instruções manuais executáveis.
11. Nunca use linguagem depreciativa sobre a capacidade do usuário.

Este protocolo não fragmenta trabalho que o agente consegue executar sozinho. GitHub, análise, auditoria, geração de documentação e verificações automatizadas continuam até o checkpoint técnico apropriado.
