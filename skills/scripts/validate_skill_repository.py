#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
ART = REPO_ROOT / "art"
SHARED = ROOT / "library"
ART_SKILLS = ART / "skills"
ARCHIVE = REPO_ROOT / "migration" / "provenance" / "historical-skills" / "library"

EXPECTED_SHARED = {"minecraft-ci-release", "minecraft-dependency-compatibility-graph", "minecraft-jar-reverse-engineering", "minecraft-modpack-bisect", "minecraft-neoforge-engineering", "minecraft-neoforge-modpack-debugging", "minecraft-testing", "modpack-inventory-redundancy-audit"}
EXPECTED_ART = {"minecraft-asset-art-direction", "minecraft-audio-design", "minecraft-blockbench-geckolib", "minecraft-spell-production", "minecraft-spell-vfx-engineering", "minecraft-vfx-engineering", "minecraft-visual-qa"}
EXPECTED_ARCHIVE = {"minecraft-commands-scripting", "minecraft-datapack", "minecraft-essentials-ops", "minecraft-imagegen", "minecraft-mod-dev", "minecraft-modding", "minecraft-multiloader", "minecraft-plugin-dev", "minecraft-resource-pack", "minecraft-server-admin", "minecraft-world-generation", "minecraft-worldedit-ops"}

def skill_set(root):
    return {p.parent.name for p in root.glob("*/SKILL.md")}

def require_set(label, actual, expected):
    if actual != expected:
        raise SystemExit(f"{label} mismatch: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

def validate_names(root):
    for path in root.glob("*/SKILL.md"):
        declared_name = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("name:"):
                declared_name = line.partition(":")[2].strip()
                break
        if declared_name != path.parent.name:
            raise SystemExit(f"invalid skill name metadata: {path}")

require_set("shared active skills", skill_set(SHARED), EXPECTED_SHARED)
require_set("art active skills", skill_set(ART_SKILLS), EXPECTED_ART)
require_set("reference-only archived skills", skill_set(ARCHIVE), EXPECTED_ARCHIVE)
validate_names(SHARED)
validate_names(ART_SKILLS)

for required in [ROOT/"README.md", ROOT/"ROUTER.md", ROOT/"VERSION-AUTHORITY.md", ROOT/"USER-GUIDED-WORKFLOW.md", ART/"VISUAL-STYLE-BIBLE.md", ART/"tooling/blockbench/asset-toolkit/asset_toolkit.js", ART/"tooling/blockbench/asset-toolkit/COMPATIBILITY.md", ART/"golden-samples/validate_golden_samples.js", ART/"golden-samples/validate_reference_evidence.js"]:
    if not required.is_file():
        raise SystemExit(f"missing Factory skill/art capability: {required.relative_to(REPO_ROOT)}")

node = shutil.which("node")
if not node:
    raise SystemExit("Node.js is required to validate Factory art tooling")
toolkit = ART / "tooling/blockbench/asset-toolkit"
subprocess.run([node, "--check", str(toolkit/"asset_toolkit.js")], check=True)
for test in sorted(toolkit.rglob("*.test.js")):
    subprocess.run([node, "--test", str(test)], check=True)
subprocess.run([node, str(toolkit/"build_toolkit_bundle.js"), "--check"], check=True)
for validator in [ART/"golden-samples/validate_golden_samples.js", ART/"golden-samples/validate_reference_evidence.js"]:
    subprocess.run([node, "--check", str(validator)], check=True)
    subprocess.run([node, str(validator)], check=True)
rendered = ART/"tooling/validators/validate_golden_reference_rendered_edges.js"
subprocess.run([node, "--check", str(rendered)], check=True)
subprocess.run([node, str(rendered), "--self-test"], check=True)
subprocess.run([node, str(rendered)], check=True)
print("OK: 15 active Factory skills, 12 reference-only historical skills, neutral Asset Toolkit, standards and Golden Samples validated")
