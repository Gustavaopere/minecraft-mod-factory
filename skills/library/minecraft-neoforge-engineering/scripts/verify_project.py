#!/usr/bin/env python3
"""Discover Gradle tasks and run only requested tasks that exist. Non-destructive."""
from __future__ import annotations
import argparse, os, re, subprocess, sys
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("tasks", nargs="*", help="Tasks to run; default: compileJava test")
ap.add_argument("--list-only", action="store_true")
args=ap.parse_args()
root=Path.cwd()
wrapper=root/("gradlew.bat" if os.name=="nt" else "gradlew")
if not wrapper.exists():
    sys.exit("No Gradle wrapper found. Run from repository root.")

def call(cmd, capture=False):
    print("$ "+" ".join(map(str,cmd)))
    return subprocess.run(cmd,cwd=root,text=True,stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None)

p=call([str(wrapper),"tasks","--all"],capture=True)
if p.returncode:
    print(p.stdout or "")
    sys.exit(p.returncode)
text=p.stdout or ""
(root/"build").mkdir(exist_ok=True)
(root/"build"/"minecraft-neoforge-engineering-gradle-tasks.txt").write_text(text,encoding="utf-8")
if args.list_only:
    print(text)
    sys.exit(0)

requested=args.tasks or ["compileJava","test"]

def exists(task):
    # Gradle task listing usually emits '<task> - description' or just '<task>'.
    return re.search(rf"(?m)^{re.escape(task)}(?:\s+-|\s*$)", text) is not None

failed=[]
for task in requested:
    if not exists(task):
        print(f"SKIP: task not found: {task}")
        continue
    r=call([str(wrapper),task])
    if r.returncode: failed.append(task)
if failed:
    sys.exit("Failed tasks: "+", ".join(failed))
print("Requested available verification tasks completed successfully.")
