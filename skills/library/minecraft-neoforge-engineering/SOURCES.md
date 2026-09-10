# Public sources and design provenance

Checked 2026-08-27.

This skill is original procedural guidance. It borrows **public design principles**, not proprietary implementation or hidden prompts.

## Agent Skills / OpenAI / Anthropic

- Agent Skills specification: https://agentskills.io/specification
- OpenAI Academy — Using skills: https://openai.com/academy/skills/
- OpenAI Help — Skills in ChatGPT: https://help.openai.com/en/articles/20001066
- Anthropic — Equipping agents for the real world with Agent Skills: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

Public principles incorporated: SKILL.md packaging, progressive disclosure, focused references, executable deterministic helpers, evaluation-oriented skill iteration, and reusable workflows.

## Runable

- Runable documentation: https://docs.runable.com/
- Runable 2.0 / Agent Skills public guide: https://runable.com/blogs/runable-2-0-agent?artifact=agent-skills

Public principles incorporated: explicit plan mode for complex work, sandboxed execution, iterative building, reusable skills, connectors/tools, memory/context, and outcome-oriented workflows. No proprietary Runable source or hidden prompt is included.

## NeoForge

- NeoForge 1.21.1 documentation: https://docs.neoforged.net/docs/1.21.1/
- Networking 1.21.1: https://docs.neoforged.net/docs/1.21.1/networking/
- Structuring 1.21.1: https://docs.neoforged.net/docs/1.21.1/gettingstarted/structuring/
- Mod files 1.21.1: https://docs.neoforged.net/docs/1.21.1/gettingstarted/modfiles/
- ModDevGradle: https://docs.neoforged.net/toolchain/docs/plugins/mdg/
- Official NeoForge source: https://github.com/neoforged/NeoForge
- Official 1.21.1 MDKs: https://github.com/NeoForgeMDKs

The skill intentionally avoids freezing most Java signatures into reference text. Exact source resolved by the project's build is required when signatures/lifecycle details are material.
