# Minecraft NeoForge Engineering Skill

Version 1.0.0. Portable Agent Skill for Minecraft **1.21.1**, **NeoForge 21.1.x**, and **Java 21**.

It is designed to improve coding-agent behavior for real mod repositories: exact-version API verification, plan-first architecture, test-first changes where meaningful, server/client safety, persistence/networking correctness, optional-mod isolation, bounded performance, systematic debugging, Git concurrency, and evidence-based completion.

## Install in ChatGPT

If your ChatGPT account/workspace exposes personal Skills:

1. Open **Plugins** in the sidebar.
2. Open the **Skills** tab.
3. Choose **Create** → **Upload from your computer**.
4. Upload the ZIP containing the `minecraft-neoforge-engineering/` directory.
5. Review the skill contents and install it.

OpenAI's current documentation says personal Skills are generally available on Business, Enterprise, Healthcare, and Edu; availability may differ by product surface/workspace. Skills are also supported in Codex/API-compatible workflows.

## Portable install

The bundle follows the open Agent Skills format. The directory name must remain `minecraft-neoforge-engineering` because the specification requires it to match the `name` in `SKILL.md`.

## Usage

You normally do not need a giant setup prompt. Ask naturally, for example:

- "Continue this NeoForge 1.21.1 mod from the real current repository state."
- "Implement a server-authoritative stamina system."
- "Audit this integration with Epic Fight."
- "Debug this dedicated-server crash."
- "Prepare this mod for release."

You may explicitly mention `minecraft-neoforge-engineering` if the client supports skill selection or @-mention.

## Repository-specific rules still win

This skill is generic engineering guidance. A repository's explicit AGENTS/README/plans/decision files can impose project-specific constraints, branch names, integration order, or release policy. The skill requires the agent to inspect and honor them.

## Scripts

All scripts are standard-library Python 3 and are advisory utilities. They do not commit, reset, merge, rebase, delete branches, or force-push.

- `scripts/preflight.py` — repository/environment snapshot.
- `scripts/inspect_repo.py` — architecture/build inventory.
- `scripts/verify_project.py` — discovers Gradle tasks, then runs only requested/available verification.
- `scripts/scan_client_leaks.py` — heuristic scan for obvious client-only imports in common source.
- `scripts/validate_skill.py` — local Agent Skills bundle checks.

Read script output; heuristics are evidence, not proof.
