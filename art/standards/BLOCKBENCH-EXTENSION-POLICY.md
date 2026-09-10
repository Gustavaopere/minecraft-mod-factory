# Blockbench Extension Policy

Status: canonical project policy for the Minecraft Mod Factory Asset Toolkit and future Minecraft Mod Factory Asset MCP.

## Authority order

For runtime-provider presence and version, the physical mod/JAR list is authoritative. Provider source/JAR contracts and official provider documentation outrank secondary descriptions. For Blockbench extensions, the official Blockbench plugin catalog and the extension's own source are authoritative for plugin ID, current version and editor compatibility. Golden Samples and the Visual Style Bible govern project acceptance, not provider/runtime identity.

Never silently preserve a stale documentation pin when the authoritative source has changed. Re-audit the affected profile before enabling it.

## Installed is not trusted

These states are independent:

1. installed;
2. version-matched;
3. compatible with the active Blockbench version;
4. trusted for the intended provider/profile;
5. explicitly MCP-authorized for the current session.

An extension becomes MCP-usable only when every required condition is true. Installation alone grants no authority.

## Human installation only

The project does not permit the MCP, sidecar or Toolkit to install arbitrary plugins, execute arbitrary JavaScript, invoke arbitrary actions by name, run shell commands, or fetch/execute unreviewed plugin code. Plugin installation and upgrades remain explicit human actions.

## Current audited provider-extension pins — 2026-09-08

| Plugin ID | Extension | Current pin | Classification | Profile use |
|---|---|---:|---|---|
| `geckolib` | GeckoLib Models & Animations | 4.2.5 | REQUIRED_PROFILE | GeckoLib 4 |
| `azurelib_utils` | AzureLib Animator | 2.1.5 | REQUIRED_PROFILE | AzureLib |
| `cem_template_loader` | CEM Template Loader | 9.2.0 | REQUIRED_PROFILE | EMF/CEM |
| `emf_animation_addon` | EMF Animation Addon | 1.0.5 | PREFERRED | EMF/CEM animation authoring |
| `animated_java` | Animated Java | 1.10.2 | OPTIONAL | display-entity/datapack-resource-pack pipeline |
| `animation_utils` | GeckoLib Animation Utils | 4.1.3 | BLOCKED_LEGACY | never MCP-enabled |

The AzureLib plugin officially advertises Blockbench 4.8.0–15.0.0, but this repository keeps MCP enablement fail-closed to the audited project baseline 5.1.6 until another editor version is tested. CEM Template Loader requires Blockbench >=5.0.0; EMF Animation Addon >=4.9.0; Animated Java >=5.1.4.

## Classifications

`REQUIRED_PROFILE` means the profile cannot be resolved without the extension. `PREFERRED` improves the supported workflow but is not a hard dependency. `OPTIONAL` is enabled only for an explicitly selected workflow. `HUMAN_ONLY`, `AUDIT_REQUIRED`, `BLOCKED_LEGACY`, `INCOMPATIBLE_EDITOR`, `LOADER_MISMATCH` and `PROVIDER_ABSENT` are fail-closed for MCP use. `DEV_ONLY` and `DISABLED_BY_DEFAULT` never become production defaults merely because they are installed.

## Re-audit trigger

Re-check the official catalog and provider source before installation, upgrade, profile activation, release qualification, or after Blockbench/provider version drift. A changed plugin ID, version, compatibility range or provider contract invalidates the previous capability proof until reviewed.
