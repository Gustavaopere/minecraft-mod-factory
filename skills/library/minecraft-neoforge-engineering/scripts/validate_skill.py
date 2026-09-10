#!/usr/bin/env python3
"""Local structural validator for this Agent Skill; does not replace official skills-ref validation."""
from pathlib import Path
import re, sys

root=Path(__file__).resolve().parents[1]
skill=root/"SKILL.md"
errors=[]
if not skill.exists(): errors.append("SKILL.md missing")
else:
    text=skill.read_text(encoding="utf-8")
    m=re.match(r"^---\n(.*?)\n---\n",text,re.S)
    if not m: errors.append("YAML frontmatter missing or malformed")
    else:
        fm=m.group(1)
        def scalar(key):
            mm=re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$",fm)
            return mm.group(1).strip().strip('"') if mm else None
        name=scalar("name"); desc=scalar("description"); comp=scalar("compatibility")
        if name != root.name: errors.append(f"name must match directory: {root.name!r}, got {name!r}")
        if not name or len(name)>64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",name or ""):
            errors.append("invalid name")
        if not desc or len(desc)>1024: errors.append("description missing or >1024 chars")
        if comp and len(comp)>500: errors.append("compatibility >500 chars")
    if len(text.splitlines())>500: errors.append("SKILL.md exceeds 500 lines")
    # verify local markdown refs one level deep from SKILL.md
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"): continue
        p=root/target
        if not p.exists(): errors.append(f"broken SKILL.md reference: {target}")
        if len(Path(target).parts)>2: errors.append(f"reference too deeply nested: {target}")

if errors:
    print("INVALID")
    for e in errors: print("- "+e)
    sys.exit(1)
print("VALID (local structural checks)")
print("For canonical validation, also run: skills-ref validate <skill-directory>")
