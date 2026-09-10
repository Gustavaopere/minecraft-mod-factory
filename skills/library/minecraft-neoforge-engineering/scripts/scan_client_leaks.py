#!/usr/bin/env python3
"""Heuristic scanner for obvious client-only imports outside client-named paths. Not a proof of classloading safety."""
from pathlib import Path
import re

root=Path.cwd()
base=root/"src"/"main"/"java"
if not base.exists(): raise SystemExit("src/main/java not found")
rx=re.compile(r"^\s*import\s+(net\.minecraft\.client\.[\w.]+|net\.neoforged\.neoforge\.client\.[\w.]+)\s*;", re.M)
findings=[]
for p in base.rglob("*.java"):
    rel=p.relative_to(root)
    # Client-named paths are still inspected separately by humans, but suppress obvious intentional locations.
    path_lower=str(rel).replace('\\','/').lower()
    likely_client=any(seg in path_lower for seg in ["/client/","clientonly","clientsetup"])
    for m in rx.finditer(p.read_text(encoding="utf-8",errors="replace")):
        if not likely_client: findings.append((str(rel),m.group(1)))
print("Heuristic findings (review manually; zero findings does NOT prove safety):")
for f,imp in findings: print(f"{f}: {imp}")
print(f"count={len(findings)}")
