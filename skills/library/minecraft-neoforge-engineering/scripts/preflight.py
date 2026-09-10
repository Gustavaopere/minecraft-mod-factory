#!/usr/bin/env python3
"""Non-destructive repository/environment snapshot for NeoForge mod work."""
from __future__ import annotations
import subprocess, sys, os
from pathlib import Path

ROOT = Path.cwd()

def run(*args: str) -> str:
    try:
        p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        return p.stdout.strip()
    except Exception as e:
        return f"<error: {e}>"

print("== repository ==")
for cmd in [("git","status","--short","--branch"), ("git","branch","--show-current"), ("git","rev-parse","HEAD"), ("git","remote","-v")]:
    print(f"$ {' '.join(cmd)}")
    print(run(*cmd))

print("\n== java ==")
print(run("java","-version"))

wrapper = ROOT / ("gradlew.bat" if os.name == "nt" else "gradlew")
print("\n== gradle ==")
if wrapper.exists():
    print(run(str(wrapper), "--version"))
else:
    print("No Gradle wrapper found in current directory.")

print("\n== build/version hints ==")
for name in ["gradle.properties","build.gradle","build.gradle.kts","settings.gradle","settings.gradle.kts"]:
    p = ROOT/name
    if not p.exists(): continue
    print(f"-- {name} --")
    for i,line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(),1):
        low=line.lower()
        if any(k in low for k in ["minecraft", "neoforge", "neo_version", "java", "moddev", "neogradle", "mapping"]):
            print(f"{i}: {line[:300]}")
