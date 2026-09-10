#!/usr/bin/env python3
"""Lightweight, non-destructive inventory of a Minecraft mod repository."""
from pathlib import Path
import re

root=Path.cwd()
print(f"root: {root}")

markers=["AGENTS.md","README.md","CONTRIBUTING.md","gradle.properties","build.gradle","build.gradle.kts","settings.gradle","settings.gradle.kts"]
print("\n== authority/build files ==")
for m in markers:
    if (root/m).exists(): print(m)
for d in ["plans",".github/workflows","src/main/java","src/main/resources","src/test/java","src/gametest"]:
    p=root/d
    if p.exists(): print(d+"/")

java=list((root/"src").rglob("*.java")) if (root/"src").exists() else []
patterns={
    "@Mod entrypoints": r"@Mod\s*\(",
    "DeferredRegister": r"DeferredRegister",
    "Event subscribers": r"EventBusSubscriber|SubscribeEvent",
    "Networking": r"RegisterPayloadHandlersEvent|CustomPacketPayload|StreamCodec",
    "SavedData": r"\bSavedData\b",
    "Attachments": r"AttachmentType|RegisterAttachmentsEvent",
    "Client imports": r"import\s+net\.minecraft\.client\.",
    "Mixins": r"org\.spongepowered\.asm\.mixin|@Mixin",
}
print(f"\njava files: {len(java)}")
for label,pat in patterns.items():
    hits=[]
    rx=re.compile(pat)
    for p in java:
        txt=p.read_text(encoding="utf-8",errors="replace")
        if rx.search(txt): hits.append(str(p.relative_to(root)))
    print(f"{label}: {len(hits)}")
    for h in hits[:12]: print("  "+h)
    if len(hits)>12: print(f"  ... +{len(hits)-12}")
