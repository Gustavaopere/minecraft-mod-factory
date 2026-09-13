# Construction C11 — Complex Modded Golden Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first deterministic, evidence-backed, multi-namespace modded Construction Golden Sample for Minecraft 1.21.1 / NeoForge 21.1.248, proving the existing C2/C4/C5/C6/C7/C8 authorities together without claiming C12 runtime acceptance.

**Architecture:** C11 starts by capturing a real C4 registry from the exact physical modpack, then freezes a deterministic C5 palette request/resolution, fixture-specific geometry, C2 Build IR, C7 structural QA, C8 preview/review evidence, C6 Sponge v3 bytes, and a closed fixture-local manifest. CI validates the frozen evidence offline, reruns C0–C10 regressions, rebuilds the existing C4 NeoForge probe, and never calls external providers or requires payment.

**Tech Stack:** Python 3.11, Java 21, NeoForge 21.1.248, existing Engineering I2 importer, Construction C2/C4/C5/C6/C7/C8 Python authorities, nbtlib through the existing hash-pinned Construction environment, GitHub Actions, SonarQube Cloud.

**Spec:** `docs/superpowers/specs/2026-09-12-construction-c11-complex-modded-golden-design.md`

## Global Constraints

- Target exactly Minecraft `1.21.1`, loader `neoforge`, NeoForge `21.1.248`, Java `21`.
- Physical modlist authority is the current 595-mod file with SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`.
- Engineering I2 remains the only physical-modlist parser/catalog authority.
- C4 remains the only block/state existence and safety authority.
- Do not invent any modded block ID or state before the real C4 registry proves it.
- C11 baseline accepts only C4 `runtime_confirmed` selections with safety exactly `ordinary`.
- Actual Build IR must use at least three namespaces total and at least two non-`minecraft` namespaces.
- Candidate decorative namespaces physically present in the authoritative modlist are `chipped` 4.0.2, `rechiseled` 1.2.5, and `supplementaries` 1.21.1-3.9.8; their block IDs are not presumed.
- Functional machines, BlockEntities, dynamic renderers, connected/multipart semantics, material-bearing blocks, and other non-ordinary C4 safety classes are out of baseline scope.
- C10 is regression-only. No external-provider network call, credential, browser automation, paid generation, EP2 proof, or user spending is allowed for C11 acceptance.
- C12 remains authoritative for full-modpack boot, live-world placement, runtime visual fidelity, CTM/tints/emissives/shaders/lighting, and functional behavior.
- `construction/STATUS.md` must not change in the implementation PR. STATUS advances only in a separate post-merge closeout.
- Every new Python source path added for C11 must have executable coverage in Factory Sonar CI; do not hide C11 source through coverage exclusions.
- Preserve current C2/C4/C5/C6/C7/C8 public contracts unless a failing C11 regression proves a concrete defect in the owning authority.
- Do not silently change source/evidence formats or introduce Git LFS/compression for `registry.json` or `expected.schem`.
- If the complete real C4 registry is impractically large for repository policy, stop implementation and revise the approved design instead of committing a subset.
- During execution, if the physical modpack/JAR set is unavailable to the agent, request exactly one manual action at the capture gate and wait for its result before continuing.

---

## File Structure

Expected implementation files and responsibilities:

- `construction/tests/test_c11_complex_modded_golden.py` — single C11 contract suite covering positive Golden reproduction, fixture-local helpers, mutation/fail-closed behavior, workflow contract, and STATUS exclusion.
- `construction/fixtures/complex-modded-golden/capture_registry.py` — fixture-local offline composition helper that reuses I2 + C4 to turn the physical modlist, the exact physical JAR directory, and a raw C4 runtime snapshot into canonical `registry.json`.
- `construction/fixtures/complex-modded-golden/registry.json` — canonical real C4 registry captured from the exact physical modpack.
- `construction/fixtures/complex-modded-golden/build-spec.json` — frozen BuildSpec v1 for the 32×14×32 industrial Golden.
- `construction/fixtures/complex-modded-golden/select_palette.py` — fixture-local deterministic policy for choosing two evidence-backed decorative mod namespaces and seven one-state ordinary blocks, then producing the C5 request/resolution.
- `construction/fixtures/complex-modded-golden/palette-request.json` — frozen C5 role request generated from real registry evidence.
- `construction/fixtures/complex-modded-golden/expected-palette-resolution.json` — frozen exact C5 output.
- `construction/fixtures/complex-modded-golden/generate.py` — deterministic fixture geometry and C2 Build IR generation; consumes C5 resolution, never a duplicate hardcoded modded block list.
- `construction/fixtures/complex-modded-golden/expected-build-ir.json` — frozen canonical C2 Build IR.
- `construction/fixtures/complex-modded-golden/expected-structural-qa.json` — frozen C7 report.
- `construction/fixtures/complex-modded-golden/c8/{front,back,left,right,top,isometric,layers}.svg` — frozen canonical C8 previews.
- `construction/fixtures/complex-modded-golden/c8/review-evidence.json` — hash-bound C8 review decisions based on the actual generated previews.
- `construction/fixtures/complex-modded-golden/c8/expected-visual-qa.json` — frozen C8 report.
- `construction/fixtures/complex-modded-golden/expected.schem` — frozen byte-stable C6 Sponge v3 output.
- `construction/fixtures/complex-modded-golden/manifest.py` — fixture-local manifest build/validation helpers.
- `construction/fixtures/complex-modded-golden/manifest.json` — closed deterministic evidence index.
- `.github/workflows/factory-construction-c11-complex-modded-golden.yml` — dedicated C11 workflow plus C0–C10 regression chain and real C4 probe build.
- `.github/workflows/factory-sonar-ci.yml` — append C11 fixture source coverage using the C11 test suite.
- `migration/full-skill-migration/test_sonar_ci_contract.py` — assert the C11 Sonar coverage target remains fail-closed and runs before scan.
- `construction/README.md` — record C11 as the complex modded offline Golden frontier and C12 as runtime acceptance.
- `construction/docs/ARCHITECTURE.md` — document C11 evidence flow and authority boundaries.
- `docs/superpowers/specs/2026-09-12-construction-c11-complex-modded-golden-design.md` — approved design, already versioned.
- `docs/superpowers/plans/2026-09-12-construction-c11-complex-modded-golden.md` — this plan.

No production C2/C4/C5/C6/C7/C8 module is listed for modification. Add one only after a RED test demonstrates a concrete owning-authority defect.

---

### Task 1: Start the implementation branch and establish the first C11 RED contract

**Files:**
- Create: `construction/tests/test_c11_complex_modded_golden.py`
- Read only: `construction/STATUS.md`
- Read only: `docs/superpowers/specs/2026-09-12-construction-c11-complex-modded-golden-design.md`

**Interfaces:**
- Consumes: approved spec and repository paths only.
- Produces: a C11 test module whose first executable contract requires a real canonical C4 registry and refuses to continue with fabricated fixture data.

- [ ] **Step 1: Re-audit before implementation**

Run:

```bash
git fetch origin main
git rev-parse origin/main
git status --short
git log -1 --oneline origin/main
```

Then inspect open PRs and changed files. If `main` advanced after the plan baseline or an open PR touches Construction C11/C4/C5/C6/C7/C8/STATUS/Sonar, reconcile or resolve the overlap before writing code.

Expected: clean worktree, exact current `main` known, no hidden concurrent C11 implementation.

- [ ] **Step 2: Create isolated implementation worktree/branch**

Use `superpowers:using-git-worktrees` when executing locally. Create:

```bash
git switch -c feat/construction-c11-complex-modded-golden
```

The branch must include the approved C11 spec and this plan. Do not change `construction/STATUS.md`.

- [ ] **Step 3: Write the first failing registry-prerequisite test**

Create `construction/tests/test_c11_complex_modded_golden.py` with the shared loader and the first contract:

```python
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "construction" / "fixtures" / "complex-modded-golden"
REGISTRY_PATH = FIXTURE / "registry.json"
C4_PATH = ROOT / "construction" / "core" / "modpack_registry.py"
PHYSICAL_MODLIST_SHA256 = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC11ComplexModdedGoldenTest(unittest.TestCase):
    def test_real_c4_registry_fixture_exists_and_is_canonical(self) -> None:
        self.assertTrue(REGISTRY_PATH.is_file(), "C11 requires captured real C4 registry evidence")
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        c4 = load_path(C4_PATH, "construction_c4_for_c11")
        self.assertEqual([], c4.validate_modpack_registry(registry))
        self.assertEqual(PHYSICAL_MODLIST_SHA256, registry["physical"]["source_sha256"])
        self.assertEqual(PHYSICAL_MODLIST_SHA256, registry["runtime"]["physical_snapshot_sha256"])
        self.assertEqual(
            {"minecraft": "1.21.1", "loader": "neoforge", "loader_version": "21.1.248"},
            registry["runtime"]["target"],
        )
```

- [ ] **Step 4: Run the RED test**

Run:

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Expected: FAIL only because `construction/fixtures/complex-modded-golden/registry.json` does not exist yet.

- [ ] **Step 5: Commit the observed RED**

```bash
git add construction/tests/test_c11_complex_modded_golden.py
git commit -m "test(construction): define C11 real registry prerequisite"
```

---

### Task 2: Implement the fixture-local C4 capture helper and obtain the real registry

**Files:**
- Create: `construction/fixtures/complex-modded-golden/capture_registry.py`
- Create after real capture: `construction/fixtures/complex-modded-golden/registry.json`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`
- Consume read-only: `engineering/tooling/import-physical-modlist.py`
- Consume read-only: `construction/core/modpack_registry.py`
- Consume read-only: `construction/scripts/prepare_neoforge_registry_probe.py`
- Consume read-only: `construction/runtime/neoforge-registry-probe/FactoryConstructionRegistryProbe.java`

**Interfaces:**
- Consumes: `parse_modlist_bytes(...)`, `index_jar_file(...)`, `build_modpack_registry(...)`, `validate_modpack_registry(...)`, `canonical_json_bytes(...)`.
- Produces: `compose_registry(physical_modlist: Path, mods_dir: Path, runtime_snapshot: Path, *, captured_at: str) -> dict` and CLI output `registry.json`.

- [ ] **Step 1: Add failing capture-helper tests before implementation**

Extend the C11 test with temporary synthetic inputs that verify:

```python
self.assertTrue((FIXTURE / "capture_registry.py").is_file())
```

and, once importable, require `compose_registry(...)` to reject a missing physical JAR before it calls C4 composition.

Use a minimal temp modlist with one `alpha-1.0.0.jar` row plus NeoForge and an empty temp `mods/` directory. Expected exception text:

```text
missing physical top-level JARs: alpha-1.0.0.jar
```

- [ ] **Step 2: Run the focused RED**

```bash
python3 -m unittest construction.tests.test_c11_complex_modded_golden.ConstructionC11ComplexModdedGoldenTest.test_capture_helper_requires_every_physical_top_level_jar -v
```

Expected: FAIL because `capture_registry.py` is absent.

- [ ] **Step 3: Implement the minimal capture helper**

`capture_registry.py` must:

```python
def compose_registry(
    physical_modlist: Path,
    mods_dir: Path,
    runtime_snapshot: Path,
    *,
    captured_at: str,
) -> dict:
    i2 = load_i2_importer()
    c4 = load_c4_registry()
    physical = i2.parse_modlist_bytes(
        physical_modlist.read_bytes(),
        captured_at=captured_at,
        source_name=physical_modlist.name,
    )
    jar_names = sorted(
        entry["jar"]
        for entry in physical["entries"]
        if entry["top_level"] and entry["jar"].lower().endswith(".jar")
    )
    missing = [name for name in jar_names if not (mods_dir / name).is_file()]
    if missing:
        raise ValueError("missing physical top-level JARs: " + ", ".join(missing))
    static_indexes = [c4.index_jar_file(mods_dir / name) for name in jar_names]
    runtime = json.loads(runtime_snapshot.read_text(encoding="utf-8"))
    registry = c4.build_modpack_registry(physical, static_indexes, runtime)
    errors = c4.validate_modpack_registry(registry)
    if errors:
        raise ValueError("invalid composed C4 registry: " + "; ".join(errors))
    return registry
```

The CLI accepts exactly:

```text
--physical-modlist PATH
--mods-dir PATH
--runtime-snapshot PATH
--captured-at STRING
--output PATH
```

It writes `c4.canonical_json_bytes(registry)` and immediately reloads/revalidates the written file.

- [ ] **Step 4: Run capture-helper unit tests GREEN**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Expected: helper contract tests PASS; the real-registry test still FAILS because physical evidence has not been captured.

- [ ] **Step 5: Materialize and build the existing C4 probe**

```bash
python3 construction/scripts/prepare_neoforge_registry_probe.py \
  --output .factory-local/c11/runtime-probe
chmod +x .factory-local/c11/runtime-probe/gradlew
(
  cd .factory-local/c11/runtime-probe
  ./gradlew test build --no-daemon
)
```

Expected: BUILD SUCCESSFUL; exactly the existing C4 probe source is embedded in the generated NeoForge project.

- [ ] **Step 6: Capture the raw runtime snapshot from the physical modpack**

The probe requires these JVM properties:

```text
-Dfactory.construction.registryOutput=<absolute-path>/c11-runtime-snapshot.json
-Dfactory.construction.physicalSnapshotSha256=7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00
```

Run the exact physical Minecraft 1.21.1 / NeoForge 21.1.248 instance with the built probe JAR added to its mod set. The probe writes the runtime snapshot on `ServerStartedEvent`.

If the agent cannot access the physical instance/JAR directory, stop here and request **one** manual action only: ask the user to run the prepared probe in that existing physical instance and return the produced `c11-runtime-snapshot.json`. Do not ask for any provider payment, subscription, or external generation.

- [ ] **Step 7: Compose the canonical real C4 registry**

With the exact physical JAR directory available, run:

```bash
python3 construction/fixtures/complex-modded-golden/capture_registry.py \
  --physical-modlist /mnt/data/modlist.txt \
  --mods-dir /absolute/path/to/the/exact/physical/mods \
  --runtime-snapshot /absolute/path/to/c11-runtime-snapshot.json \
  --captured-at 2026-09-09 \
  --output construction/fixtures/complex-modded-golden/registry.json
```

If `/mnt/data/modlist.txt` is not available in the execution environment, use the exact authoritative 595-mod source with the same SHA-256. Do not reconstruct the modlist from memory.

- [ ] **Step 8: Validate the captured evidence**

Run:

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
python3 - <<'PY'
import hashlib, json
from pathlib import Path
p = Path('construction/fixtures/complex-modded-golden/registry.json')
data = p.read_bytes()
print('registry_file_sha256', hashlib.sha256(data).hexdigest())
doc = json.loads(data)
print('registry_content_sha256', doc['content_sha256'])
print('physical_sha256', doc['physical']['source_sha256'])
print('block_count', len(doc['blocks']))
PY
```

Expected: C4 validation PASS, physical/runtime SHA exact, target exact, non-zero real block count.

- [ ] **Step 9: Commit the helper and real registry together**

```bash
git add \
  construction/fixtures/complex-modded-golden/capture_registry.py \
  construction/fixtures/complex-modded-golden/registry.json \
  construction/tests/test_c11_complex_modded_golden.py
git commit -m "feat(construction): capture C11 real modpack registry"
```

Do not proceed if the registry was hand-authored, reduced to a subset, or produced without the exact physical JAR set.

---

### Task 3: Freeze BuildSpec and deterministic C5 palette evidence

**Files:**
- Create: `construction/fixtures/complex-modded-golden/build-spec.json`
- Create: `construction/fixtures/complex-modded-golden/select_palette.py`
- Create: `construction/fixtures/complex-modded-golden/palette-request.json`
- Create: `construction/fixtures/complex-modded-golden/expected-palette-resolution.json`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`

**Interfaces:**
- Consumes: validated `registry.json`, C5 `resolve_palette(build_spec, registry, request) -> dict`.
- Produces: deterministic `derive_palette_request(registry: dict) -> dict` and exact frozen C5 resolution.

- [ ] **Step 1: Add RED tests for BuildSpec, roles, namespaces, and safety**

Add constants:

```python
BUILD_SPEC_PATH = FIXTURE / "build-spec.json"
PALETTE_REQUEST_PATH = FIXTURE / "palette-request.json"
PALETTE_RESOLUTION_PATH = FIXTURE / "expected-palette-resolution.json"
EXPECTED_ROLES = (
    "structural_frame",
    "wall_cladding",
    "flooring",
    "roofing",
    "accent_trim",
    "window_or_grille",
    "walkway",
)
```

Tests require:

- BuildSpec target 1.21.1 / neoforge and `modpack_snapshot == registry["physical"]["source_sha256"]`.
- `max_size == {"x": 32, "y": 14, "z": 32}`.
- `allow_modded is True`.
- `allowed_namespaces == ["minecraft", "chipped", "rechiseled", "supplementaries"]`.
- exact required spaces: `production_hall`, `maintenance_mezzanine`, `loading_bay`, `utility_annex`, `service_corridor`.
- exactly seven roles in canonical role order.
- every request role has `allowed_safety == ["ordinary"]`.
- recomputing C5 produces exact equality with `expected-palette-resolution.json`.
- every selected candidate has authority `runtime_confirmed`, safety `ordinary`, and a non-null one-state `selected_state`.
- selected modded namespaces contain at least two distinct non-`minecraft` values.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Expected: failures for missing BuildSpec/palette artifacts only.

- [ ] **Step 3: Create the frozen BuildSpec**

Use exactly:

```json
{
  "schema_version": 1,
  "identity": {
    "name": "complex-modded-golden",
    "seed": 11011,
    "description": "C11 deterministic industrial/tech multi-namespace Golden"
  },
  "target": {
    "minecraft_version": "1.21.1",
    "loader": "neoforge",
    "modpack_snapshot": "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
  },
  "geometry": {
    "max_size": {"x": 32, "y": 14, "z": 32},
    "terrain_policy": "flat",
    "architectural_brief": "Medium industrial production hall with mezzanine, loading bay, utility annex, service circulation, repeated frame rhythm and contrasting cladding.",
    "required_spaces": [
      "production_hall",
      "maintenance_mezzanine",
      "loading_bay",
      "utility_annex",
      "service_corridor"
    ]
  },
  "palette": {
    "allow_modded": true,
    "allowed_namespaces": ["minecraft", "chipped", "rechiseled", "supplementaries"],
    "forbidden_blocks": []
  },
  "qa": {
    "require_walkability": true,
    "require_complete_interior": false,
    "require_determinism": true
  },
  "outputs": {"formats": ["sponge_v3"]}
}
```

- [ ] **Step 4: Implement deterministic evidence-backed palette selection**

`select_palette.py` defines:

```python
PREFERRED_MOD_NAMESPACES = ("chipped", "rechiseled", "supplementaries")
MODDED_ROLE_ASSIGNMENT = (
    "structural_frame",
    "wall_cladding",
    "roofing",
    "accent_trim",
    "window_or_grille",
    "walkway",
)
```

Eligible candidate predicate:

```python
def eligible(block: dict) -> bool:
    return (
        block["available"] is True
        and block["authority"] == "runtime_confirmed"
        and block["safety"] == "ordinary"
        and len(block["states"]) == 1
    )
```

Selection policy is deterministic and evidence-only:

1. build sorted eligible block-ID lists for `chipped`, `rechiseled`, `supplementaries`;
2. choose the first two namespaces in that fixed preference order with at least three eligible blocks each;
3. fail if fewer than two namespaces qualify;
4. map namespace A IDs `[0:3]` to `structural_frame`, `roofing`, `window_or_grille`;
5. map namespace B IDs `[0:3]` to `wall_cladding`, `accent_trim`, `walkway`;
6. require `minecraft:stone_bricks` to be real C4 `runtime_confirmed`, ordinary, exactly one state; use it for `flooring`;
7. each request role uses its selected evidence-backed block only as `preferred_block_ids=[block_id]`, `required_terms=[]`, `preferred_namespaces=[namespace]`, `allowed_safety=["ordinary"]`, and `required_state_properties={}`.

The helper must not contain any modded block ID literal.

- [ ] **Step 5: Generate and freeze request/resolution**

Give `select_palette.py` a CLI:

```text
--registry PATH
--build-spec PATH
--request-output PATH
--resolution-output PATH
```

Run:

```bash
python3 construction/fixtures/complex-modded-golden/select_palette.py \
  --registry construction/fixtures/complex-modded-golden/registry.json \
  --build-spec construction/fixtures/complex-modded-golden/build-spec.json \
  --request-output construction/fixtures/complex-modded-golden/palette-request.json \
  --resolution-output construction/fixtures/complex-modded-golden/expected-palette-resolution.json
```

- [ ] **Step 6: Run GREEN and prove two modded namespaces**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Also print only evidence-backed selections:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('construction/fixtures/complex-modded-golden/expected-palette-resolution.json')
r = json.loads(p.read_text())
for role in r['roles']:
    s = role['selected']
    print(role['role'], s['block'], s['namespace'], s['authority'], s['safety'])
PY
```

Expected: seven roles, all runtime_confirmed/ordinary, at least two non-minecraft namespaces.

- [ ] **Step 7: Commit palette evidence**

```bash
git add construction/fixtures/complex-modded-golden construction/tests/test_c11_complex_modded_golden.py
git commit -m "feat(construction): freeze C11 modded palette evidence"
```

---

### Task 4: Generate deterministic industrial geometry and freeze the C2 Build IR

**Files:**
- Create: `construction/fixtures/complex-modded-golden/generate.py`
- Create: `construction/fixtures/complex-modded-golden/expected-build-ir.json`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`

**Interfaces:**
- Consumes: frozen BuildSpec, registry, request, exact C5 resolution; C2 `canonicalize_build_ir(...)`.
- Produces: `generate_golden() -> dict` and canonical `expected-build-ir.json`.

- [ ] **Step 1: Add RED tests for generator and complexity**

Require:

```python
actual = generator.generate_golden()
expected = json.loads(EXPECTED_BUILD_IR_PATH.read_text(encoding="utf-8"))
self.assertEqual(expected, actual)
self.assertEqual(actual, generator.generate_golden())
self.assertGreater(len(actual["blocks"]), 110)
self.assertEqual({"x": 32, "y": 14, "z": 32}, actual["bounds"]["size"])
```

Compute namespaces from palette entries actually referenced by placements, then require at least three total and two non-minecraft.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Expected: missing generator/expected IR failures.

- [ ] **Step 3: Implement the fixture generator without duplicate modded IDs**

`generate.py` loads the exact frozen palette resolution, recomputes C5, requires exact equality, then creates `role_to_state` only from `selected.selected_state`.

Use a coordinate map so later geometry intentionally replaces earlier material without creating duplicate C2 placements:

```python
cells: dict[tuple[int, int, int], str] = {}

def fill(role: str, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int) -> None:
    for y in range(y0, y1 + 1):
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                cells[(x, y, z)] = role
```

Build this exact massing:

1. `flooring`: base slab `(0,0,0)..(31,0,31)`.
2. `structural_frame`: perimeter columns at x/z coordinates `{0,5,10,15,20,25,31}` where the other horizontal axis is `0` or `31`, y `1..10`.
3. `wall_cladding`: exterior walls y `1..9` on x `0/31` and z `0/31`.
4. Loading bay opening: remove cells on front `z=0`, `x=11..20`, `y=1..5`.
5. `window_or_grille`: replace facade bands y `4..5` on x walls for z `4..27`, and on back wall z=31 for x `4..27`, without closing the loading-bay opening.
6. `roofing`: main roof `(0,10,0)..(31,10,31)`.
7. `walkway`: mezzanine slab `(2,5,4)..(14,5,18)` plus one-block-wide service bridge `(14,5,11)..(26,5,11)`.
8. `structural_frame`: mezzanine supports at `(2,1..4,4)`, `(14,1..4,4)`, `(2,1..4,18)`, `(14,1..4,18)`.
9. Utility annex: `wall_cladding` walls around x `21..30`, z `21..30`, y `1..7`, with interior left open; `roofing` roof `(21,8,21)..(30,8,30)`.
10. `accent_trim`: continuous trim on the outer main-hall perimeter at y `9` and annex perimeter at y `7`, overwriting cladding where needed.

For the loading-bay removal, use:

```python
for y in range(1, 6):
    for x in range(11, 21):
        cells.pop((x, y, 0), None)
```

Convert sorted coordinate/role pairs into placements with the C5-selected state and call:

```python
canonicalize_build_ir(
    build_spec,
    placements,
    producer="factory-c11-complex-modded-golden",
    producer_version="1",
)
```

- [ ] **Step 4: Generate the first canonical IR**

```bash
python3 construction/fixtures/complex-modded-golden/generate.py \
  > construction/fixtures/complex-modded-golden/expected-build-ir.json
```

The CLI must emit `json.dumps(generate_golden(), indent=2, ensure_ascii=False) + "\n"`.

- [ ] **Step 5: Run GREEN and record frozen fixture metrics in tests**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Once the first evidence-backed IR is produced, add exact assertions for its observed `len(blocks)`, `len(palette)`, and `content_sha256`. These are fixture regression constants only; do not generalize them into C2/C7.

- [ ] **Step 6: Commit Build IR Golden**

```bash
git add construction/fixtures/complex-modded-golden/generate.py construction/fixtures/complex-modded-golden/expected-build-ir.json construction/tests/test_c11_complex_modded_golden.py
git commit -m "feat(construction): add C11 complex modded Build IR golden"
```

---

### Task 5: Freeze C7 structural QA without hiding deferments

**Files:**
- Create: `construction/fixtures/complex-modded-golden/expected-structural-qa.json`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`

**Interfaces:**
- Consumes: C7 `run_structural_qa(build_spec, build_ir, registry) -> dict` and `validate_structural_qa_report(report)`.
- Produces: exact deterministic C7 report with zero `FAIL` and an explicitly frozen DEFERRED set.

- [ ] **Step 1: Add RED structural-QA test**

```python
actual = c7.run_structural_qa(build_spec, build_ir, registry)
expected = json.loads(EXPECTED_STRUCTURAL_QA_PATH.read_text(encoding="utf-8"))
self.assertEqual(expected, actual)
c7.validate_structural_qa_report(actual)
self.assertFalse([c for c in actual["checks"] if c["status"] == "FAIL"])
self.assertEqual(
    {c["id"] for c in expected["checks"] if c["status"] == "DEFERRED"},
    {c["id"] for c in actual["checks"] if c["status"] == "DEFERRED"},
)
```

- [ ] **Step 2: Run RED**

Expected: missing `expected-structural-qa.json` only.

- [ ] **Step 3: Generate the C7 report through the existing authority**

Use a small one-shot Python command importing `structural_qa.py`, loading the exact fixture inputs, calling `run_structural_qa`, and writing canonical pretty JSON with one trailing newline.

Do not edit C7 statuses by hand. If any C7 check returns `FAIL`, fix C11 geometry or palette evidence and regenerate downstream artifacts; do not weaken C7.

- [ ] **Step 4: Run GREEN**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Expected: exact report equality, zero FAIL, deterministic DEFERRED set.

- [ ] **Step 5: Commit C7 Golden**

```bash
git add construction/fixtures/complex-modded-golden/expected-structural-qa.json construction/tests/test_c11_complex_modded_golden.py
git commit -m "feat(construction): freeze C11 structural QA evidence"
```

---

### Task 6: Generate C8 previews, review actual evidence, and freeze Visual QA

**Files:**
- Create: `construction/fixtures/complex-modded-golden/c8/front.svg`
- Create: `construction/fixtures/complex-modded-golden/c8/back.svg`
- Create: `construction/fixtures/complex-modded-golden/c8/left.svg`
- Create: `construction/fixtures/complex-modded-golden/c8/right.svg`
- Create: `construction/fixtures/complex-modded-golden/c8/top.svg`
- Create: `construction/fixtures/complex-modded-golden/c8/isometric.svg`
- Create: `construction/fixtures/complex-modded-golden/c8/layers.svg`
- Create: `construction/fixtures/complex-modded-golden/c8/review-evidence.json`
- Create: `construction/fixtures/complex-modded-golden/c8/expected-visual-qa.json`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`

**Interfaces:**
- Consumes: C8 `render_canonical_views(build_ir) -> dict[str, bytes]` and `run_visual_qa(build_spec, build_ir, views, structural_report, palette_resolution, review_evidence) -> dict`.
- Produces: seven exact SVG byte artifacts, current hash-bound review evidence, exact Visual QA report.

- [ ] **Step 1: Add RED preview integrity tests**

Require `VIEW_IDS = ("front", "back", "left", "right", "top", "isometric", "layers")` and compare each checked-in file byte-for-byte with `render_canonical_views(build_ir)`.

- [ ] **Step 2: Generate the seven canonical SVGs**

Use the existing `construction/qa/preview_renderer.py` only. Write each returned byte array directly to `c8/<view>.svg`.

Run the test and require all seven byte comparisons PASS.

- [ ] **Step 3: Review the actual generated previews before writing PASS decisions**

Inspect the rendered C11 SVGs themselves. Do not copy C3 review prose.

Create `review-evidence.json` with:

```json
{
  "schema_version": 1,
  "build_spec_sha256": "<computed by C2>",
  "build_ir_sha256": "<computed by C2>",
  "renderer_version": "c8-svg-v1",
  "views": [
    {"id": "front", "sha256": "<actual hash>"},
    {"id": "back", "sha256": "<actual hash>"},
    {"id": "left", "sha256": "<actual hash>"},
    {"id": "right", "sha256": "<actual hash>"},
    {"id": "top", "sha256": "<actual hash>"},
    {"id": "isometric", "sha256": "<actual hash>"},
    {"id": "layers", "sha256": "<actual hash>"}
  ],
  "reviewer": {"kind": "agent", "id": "openai-gpt-5.6-sol"},
  "decisions": []
}
```

Replace every `<computed...>`/`<actual...>` token immediately from the generated artifacts before committing; no placeholder may remain in the repository.

The six decision records are exactly:

- `silhouette_readability`, allowed views: front/back/left/right/top/isometric;
- `proportion`, allowed views: front/back/left/right/top/isometric;
- `material_hierarchy`, allowed views: all seven;
- `repetition`, allowed views: front/back/left/right/top/isometric;
- `facade_readability`, allowed views: front/back/left/right/isometric;
- `interior_density`, allowed views: top/isometric/layers.

Record `PASS` only when the actual SVG evidence supports the claim. If a required subjective check is `FAIL`, revise C11 geometry and regenerate all downstream evidence before freezing review evidence.

- [ ] **Step 4: Add and run Visual QA exact-equality tests**

Call:

```python
actual = c8.run_visual_qa(
    build_spec,
    build_ir,
    views,
    structural_report=structural_report,
    palette_resolution=palette_resolution,
    review_evidence=review_evidence,
)
```

Require exact equality with `expected-visual-qa.json`, zero required subjective FAIL, and:

```python
runtime = next(c for c in actual["checks"] if c["id"] == "runtime_visual_fidelity")
self.assertEqual("DEFERRED", runtime["status"])
self.assertFalse(runtime["required"])
```

- [ ] **Step 5: Freeze expected Visual QA**

Write the exact `run_visual_qa(...)` output as canonical pretty JSON plus trailing newline.

- [ ] **Step 6: Commit C8 evidence**

```bash
git add construction/fixtures/complex-modded-golden/c8 construction/tests/test_c11_complex_modded_golden.py
git commit -m "feat(construction): freeze C11 visual QA evidence"
```

---

### Task 7: Freeze C6 Sponge v3 bytes and the closed C11 manifest

**Files:**
- Create: `construction/fixtures/complex-modded-golden/expected.schem`
- Create: `construction/fixtures/complex-modded-golden/manifest.py`
- Create: `construction/fixtures/complex-modded-golden/manifest.json`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`

**Interfaces:**
- Consumes: C6 `export_sponge_v3(build_ir, required_mods=(), block_entities=()) -> bytes`, `validate_sponge_v3(payload) -> list[str]`.
- Produces: exact `.schem` bytes plus `build_manifest(fixture_root: Path) -> dict` and `validate_manifest(manifest: dict, fixture_root: Path) -> list[str]`.

- [ ] **Step 1: Add RED C6 byte-stability test**

Derive required mods from actually used Build IR namespaces:

```python
used = {
    build_ir["palette"][block["palette_index"]]["name"].split(":", 1)[0]
    for block in build_ir["blocks"]
}
required_mods = tuple(sorted(used - {"minecraft"}))
actual = c6.export_sponge_v3(build_ir, required_mods=required_mods, block_entities=())
self.assertEqual(EXPECTED_SCHEM_PATH.read_bytes(), actual)
self.assertEqual([], c6.validate_sponge_v3(actual))
```

Expected RED: missing `expected.schem`.

- [ ] **Step 2: Generate `expected.schem` only through C6**

Write `export_sponge_v3(...)` bytes directly. Never create or edit the binary through text tooling.

- [ ] **Step 3: Define the closed manifest contract in `manifest.py`**

Use exactly these top-level keys:

```python
MANIFEST_KEYS = {
    "schema_version",
    "fixture",
    "target",
    "physical_snapshot_sha256",
    "registry_content_sha256",
    "build_ir_content_sha256",
    "renderer_version",
    "sponge_version",
    "minecraft_data_version",
    "files",
}
```

`files` uses exactly these logical names and SHA-256 values:

```text
registry
build_spec
palette_request
palette_resolution
build_ir
structural_qa
front_svg
back_svg
left_svg
right_svg
top_svg
isometric_svg
layers_svg
review_evidence
visual_qa
schematic
```

`build_manifest(...)` computes file SHA-256 from exact bytes, reads authority fingerprints from the current artifacts, and emits:

```python
{
    "schema_version": 1,
    "fixture": "complex-modded-golden",
    "target": {
        "minecraft": "1.21.1",
        "loader": "neoforge",
        "loader_version": "21.1.248",
    },
    "physical_snapshot_sha256": registry["physical"]["source_sha256"],
    "registry_content_sha256": registry["content_sha256"],
    "build_ir_content_sha256": build_ir["content_sha256"],
    "renderer_version": "c8-svg-v1",
    "sponge_version": 3,
    "minecraft_data_version": 3955,
    "files": {...},
}
```

`validate_manifest(...)` rejects any top-level or file-map key mismatch and recomputes every expected hash/fingerprint from disk.

- [ ] **Step 4: Add RED/GREEN manifest tests**

RED before `manifest.py`/`manifest.json`; then implement and require:

```python
expected = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
actual = manifest_module.build_manifest(FIXTURE)
self.assertEqual(expected, actual)
self.assertEqual([], manifest_module.validate_manifest(expected, FIXTURE))
```

- [ ] **Step 5: Generate and freeze `manifest.json`**

The CLI in `manifest.py` prints canonical pretty JSON with one trailing newline. Run it to create `manifest.json`.

- [ ] **Step 6: Run the full C11 test file GREEN**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

- [ ] **Step 7: Commit C6 + manifest evidence**

```bash
git add construction/fixtures/complex-modded-golden/expected.schem construction/fixtures/complex-modded-golden/manifest.py construction/fixtures/complex-modded-golden/manifest.json construction/tests/test_c11_complex_modded_golden.py
git commit -m "feat(construction): add C11 schematic and evidence manifest"
```

---

### Task 8: Add explicit C11 mutation tests for every fail-closed boundary

**Files:**
- Modify: `construction/tests/test_c11_complex_modded_golden.py`

**Interfaces:**
- Consumes: all frozen fixture artifacts and fixture-local helpers.
- Produces: regression proof that C11 cannot pass stale, unsafe, or mismatched evidence.

- [ ] **Step 1: Add registry and target mutation tests**

Use `copy.deepcopy` and recompute C4 hashes only when the mutation is intended to reach a downstream boundary.

Required tests:

- physical SHA mismatch;
- runtime physical-link mismatch;
- registry `content_sha256` mismatch;
- wrong runtime Minecraft version;
- wrong loader version;
- selected block changed to `static_only_unconfirmed`;
- selected safety changed to `block_entity`.

Each must raise C4/C5/C11 validation failure; no test may repair the mutated input.

- [ ] **Step 2: Add palette mutation tests**

Mutate:

- request preferred block;
- resolution registry fingerprint;
- resolution selected state;
- role omission;
- role duplicate;
- safety != ordinary.

Expected: C5 or C11 exact-equality contract rejects each mutation.

- [ ] **Step 3: Add Build IR/C7 mutation tests**

Mutate:

- Build IR `content_sha256`;
- duplicate coordinate;
- coordinate outside bounds;
- palette block not present in C4 evidence;
- structural report input fingerprint;
- structural report check status to `FAIL`;
- add one additional `DEFERRED` check or change a previously non-DEFERRED check to DEFERRED.

Expected: C2/C7 validation or C11 exact report contract rejects each mutation.

- [ ] **Step 4: Add C8 mutation tests**

Mutate:

- one SVG byte;
- one review-evidence view hash;
- one review decision to required `FAIL`;
- Build IR hash in review evidence;
- renderer version.

Expected: `run_visual_qa(...)` raises `VisualQAError` or produces a report unequal to the frozen Golden.

- [ ] **Step 5: Add C6/manifest mutation tests**

Mutate:

- one byte of `.schem`;
- manifest file SHA;
- manifest authority fingerprint;
- add unknown manifest top-level key;
- add unknown manifest file-map key.

Expected: C6 or `validate_manifest(...)` rejects each mutation.

- [ ] **Step 6: Run full C11 suite**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
```

Expected: all positive and mutation tests PASS.

- [ ] **Step 7: Commit fail-closed coverage**

```bash
git add construction/tests/test_c11_complex_modded_golden.py
git commit -m "test(construction): harden C11 fail-closed boundaries"
```

---

### Task 9: Add C11 CI and Sonar coverage integration

**Files:**
- Create: `.github/workflows/factory-construction-c11-complex-modded-golden.yml`
- Modify: `.github/workflows/factory-sonar-ci.yml`
- Modify: `migration/full-skill-migration/test_sonar_ci_contract.py`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`

**Interfaces:**
- Consumes: existing pinned workflow action SHAs, existing C0–C10 test commands, existing C4 probe materialization.
- Produces: dedicated C11 workflow and fail-closed Sonar coverage registration for C11 fixture Python source.

- [ ] **Step 1: Add RED workflow-contract test**

In the C11 test require the workflow file to contain:

- `name: Factory Construction C11 Complex Modded Golden`;
- read-only contents permission;
- pinned checkout SHA `11d5960a326750d5838078e36cf38b85af677262`;
- pinned setup-python SHA `a26af69be951a213d495a4c3e4e4022e16d87065`;
- pinned setup-java SHA `cf277c60eb25467037889841efdb72551f06f6c3`;
- Python 3.11 and Java 21;
- I2 tests;
- `test_c11_complex_modded_golden.py`;
- C10 tests + `validate_c10.py`;
- C9 direct + stdio;
- C8, C7, C6, C5, C4, C3, C2, C0;
- C4 probe materialization and `./gradlew test build --no-daemon`;
- `git diff --check`;
- no provider URL/curl/browser invocation.

Run RED and expect missing workflow.

- [ ] **Step 2: Create the dedicated C11 workflow**

Follow the C10 workflow structure, but make C11 the primary contract step. Use a single job `c11-complex-modded-golden` on `ubuntu-24.04`.

Path filters must include:

```text
.github/workflows/factory-construction-c11-complex-modded-golden.yml
engineering/tooling/import-physical-modlist.py
engineering/tests/test_i2_modlist_catalog.py
engineering/tests/test_i2_security_review.py
construction/fixtures/complex-modded-golden/**
construction/tests/test_c11_complex_modded_golden.py
construction/core/build_ir.py
construction/core/modpack_registry.py
construction/core/modded_palette.py
construction/core/sponge_v3.py
construction/core/structural_qa.py
construction/core/visual_qa.py
construction/qa/**
construction/schemas/**
construction/runtime/neoforge-registry-probe/**
construction/scripts/prepare_neoforge_registry_probe.py
construction/providers/**
construction/tests/test_c10_*.py
construction/tests/test_c9_agent_mcp.py
construction/tests/test_c9_mcp_stdio.py
construction/tests/test_c8_visual_qa.py
construction/tests/test_c8_palette_resolution_contract.py
construction/tests/test_c7_architecture_qa.py
construction/tests/test_c7_registry_authority.py
construction/tests/test_c6_sponge_v3.py
construction/tests/test_c5_modded_palette.py
construction/tests/test_c4_modpack_registry.py
construction/tests/test_c4_runtime_registry_probe.py
construction/tests/test_c3_vanilla_golden.py
construction/tests/test_c2_build_ir.py
construction/tests/test_c0_foundation.py
docs/superpowers/specs/2026-09-12-construction-c11-complex-modded-golden-design.md
docs/superpowers/plans/2026-09-12-construction-c11-complex-modded-golden.md
construction/README.md
construction/docs/ARCHITECTURE.md
construction/STATUS.md
```

The workflow must not attempt the physical C4 recapture. It validates checked-in `registry.json` offline and separately rebuilds the existing C4 probe project.

- [ ] **Step 3: Add C11 source coverage to Factory Sonar CI through TDD**

First extend `migration/full-skill-migration/test_sonar_ci_contract.py` to require:

```python
self.assertIn("construction/tests/test_c11_complex_modded_golden.py", workflow)
self.assertIn("--source=construction/fixtures/complex-modded-golden", workflow)
```

Run:

```bash
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
```

Expected RED: both C11 coverage assertions fail.

Then append a C11 coverage block to `.github/workflows/factory-sonar-ci.yml` after the C10 block:

```bash
if [[ -f construction/tests/test_c11_complex_modded_golden.py && -d construction/fixtures/complex-modded-golden ]]; then
  if [[ "$coverage_started" -eq 0 ]]; then
    python3 -m coverage run \
      --branch \
      --source=construction/fixtures/complex-modded-golden \
      -m unittest construction/tests/test_c11_complex_modded_golden.py -v
  else
    python3 -m coverage run \
      --append \
      --branch \
      --source=construction/fixtures/complex-modded-golden \
      -m unittest construction/tests/test_c11_complex_modded_golden.py -v
  fi
  coverage_started=1
fi
```

Do not alter `.github/sonar/python-coverage-lock.txt` unless an actual dependency change is separately proven necessary.

- [ ] **Step 4: Run CI contract tests locally**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit C11 workflow/Sonar integration**

```bash
git add \
  .github/workflows/factory-construction-c11-complex-modded-golden.yml \
  .github/workflows/factory-sonar-ci.yml \
  migration/full-skill-migration/test_sonar_ci_contract.py \
  construction/tests/test_c11_complex_modded_golden.py
git commit -m "ci(construction): gate C11 complex modded golden"
```

---

### Task 10: Document C11 boundaries without advancing STATUS

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify: `construction/STATUS.md`

**Interfaces:**
- Consumes: implemented/frozen C11 behavior.
- Produces: architecture documentation that accurately states what C11 proves and what remains C12.

- [ ] **Step 1: Add a RED documentation-presence assertion**

Extend the C11 test to require both docs to mention:

```text
C11 Complex Modded Golden
runtime_confirmed
C12 Runtime Acceptance
```

and to assert `construction/STATUS.md` still contains:

```text
PHASE=C10_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C11_COMPLEX_MODDED_GOLDEN
```

- [ ] **Step 2: Run RED**

Expected: docs assertion fails if C11 text is not yet present; STATUS assertion passes.

- [ ] **Step 3: Update README/ARCHITECTURE only**

Document:

- real C4 registry capture is a one-time evidence prerequisite;
- CI consumes the frozen registry and does not fake full physical recapture;
- C5 selects only runtime_confirmed ordinary states;
- C11 composes C2/C4/C5/C6/C7/C8;
- C10 is regression-only;
- C12 owns live/full-modpack runtime acceptance;
- C11 implementation does not advance STATUS.

- [ ] **Step 4: Run GREEN + whitespace**

```bash
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
git diff --check
```

- [ ] **Step 5: Commit documentation**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md construction/tests/test_c11_complex_modded_golden.py
git commit -m "docs(construction): document C11 golden boundary"
```

---

### Task 11: Run the complete implementation gate, reconcile concurrency, and merge the C11 implementation PR

**Files:**
- No new production file expected.
- Potentially modify only files required by a concrete failing gate.
- Do not modify `construction/STATUS.md`.

**Interfaces:**
- Consumes: complete implementation branch.
- Produces: frozen merge-ready head with all applicable gates terminal green.

- [ ] **Step 1: Re-audit main and open PRs before the final gate**

Compare the feature branch to current `main`. If Engineering I9 or any other work merged, audit changed filenames and reconcile `main` into C11 without rebase/force. Re-run every gate after any reconciliation commit.

- [ ] **Step 2: Run the local C11 + regression suite**

Use the exact commands encoded in the new C11 workflow. At minimum:

```bash
python3 -m unittest engineering/tests/test_i2_modlist_catalog.py engineering/tests/test_i2_security_review.py -v
python3 -m unittest construction/tests/test_c11_complex_modded_golden.py -v
python3 -m unittest discover -s construction/tests -p 'test_c10_*.py' -v
python3 construction/scripts/validate_c10.py
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
python3 -m unittest construction/tests/test_c8_visual_qa.py construction/tests/test_c8_palette_resolution_contract.py -v
python3 -m unittest construction/tests/test_c7_architecture_qa.py construction/tests/test_c7_registry_authority.py -v
python3 -m unittest construction/tests/test_c6_sponge_v3.py -v
python3 -m unittest construction/tests/test_c5_modded_palette.py -v
python3 -m unittest construction/tests/test_c4_modpack_registry.py construction/tests/test_c4_runtime_registry_probe.py -v
python3 -m unittest construction/tests/test_c3_vanilla_golden.py -v
python3 -m unittest construction/tests/test_c2_build_ir.py -v
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
```

- [ ] **Step 3: Build the C4 NeoForge probe exactly as CI does**

```bash
rm -rf .factory-ci/c11/runtime-probe .factory-ci/c11/gradle-home
python3 construction/scripts/prepare_neoforge_registry_probe.py --output .factory-ci/c11/runtime-probe
chmod +x .factory-ci/c11/runtime-probe/gradlew
(
  cd .factory-ci/c11/runtime-probe
  GRADLE_USER_HOME="$PWD/../../gradle-home" ./gradlew test build --no-daemon
)
```

Expected: BUILD SUCCESSFUL under Java 21 / NeoForge 21.1.248.

- [ ] **Step 4: Prove implementation diff boundaries**

Require:

- `construction/STATUS.md` absent from changed filenames;
- no provider secret/credential;
- no HTTP/browser/scraping code;
- no C12 full-modpack boot/placement code;
- no parallel I2 parser/C4 registry/C5 resolver/C6 exporter/C8 renderer;
- exact real `registry.json`, not synthetic fixture data.

- [ ] **Step 5: Open the implementation PR as draft while CI runs**

Title:

```text
feat(construction): add C11 complex modded golden
```

PR body must state:

- exact physical modlist SHA;
- real C4 registry file/content hashes;
- selected actual namespaces and block IDs from C5 evidence;
- Build IR content SHA and frozen complexity metrics;
- C7 overall status and exact DEFERRED set;
- C8 review state and runtime_visual_fidelity DEFERRED;
- C6 `.schem` SHA and validation PASS;
- no external-provider execution/payment;
- no C12 claim;
- `construction/STATUS.md` intentionally unchanged pending post-merge validation.

- [ ] **Step 6: Wait for every applicable workflow to reach terminal success**

Inventory all workflow runs associated with the exact feature HEAD, including C11, C0–C10 workflows triggered by touched paths, Governance, Sonar, and Full Skill Migration when triggered.

Do not infer success from a subset. Fix only concrete failures with RED/GREEN evidence and rerun from the new exact HEAD.

- [ ] **Step 7: Resolve review blockers and freeze the exact head**

Require zero unresolved review threads, `mergeable=true`, and no newer `main` commit after the last reconciliation.

- [ ] **Step 8: Merge with expected-head protection**

Merge only with the exact frozen head SHA. Record the merge SHA returned by GitHub.

---

### Task 12: Validate the exact merged C11 implementation on main

**Files:**
- Read-only validation only.
- Do not modify `construction/STATUS.md` yet.

**Interfaces:**
- Consumes: exact implementation merge SHA on `main`.
- Produces: objective post-merge evidence required before STATUS closeout.

- [ ] **Step 1: Confirm `main` equals the returned merge SHA**

Verify merge parents and signature/verification state. If `main` advanced again, distinguish the C11 merge SHA from later commits and re-evaluate whether any later change overlaps C11 before closeout.

- [ ] **Step 2: Inventory every workflow run on the exact merge SHA**

Require every applicable run terminal `SUCCESS`; explicitly classify failure/cancelled/skipped/queued/in-progress counts rather than assuming missing runs are green.

- [ ] **Step 3: Revalidate merged C11 evidence bytes**

On the exact merge SHA verify:

- `registry.json` C4 validation;
- physical SHA `7c0a23...`;
- exact C5 recomputation;
- exact C2 IR regeneration and content SHA;
- exact C7 report;
- all seven exact C8 SVG bytes;
- current review-evidence hashes;
- exact C8 report with runtime_visual_fidelity DEFERRED;
- exact C6 `.schem` bytes and validator PASS;
- exact manifest validation.

- [ ] **Step 4: Re-audit open PRs before closeout**

No STATUS closeout branch may start from stale `main` without auditing concurrent work.

---

### Task 13: Close C11 with a separate STATUS-only PR

**Files:**
- Modify only: `construction/STATUS.md`

**Interfaces:**
- Consumes: exact post-merge C11 implementation SHA and workflow/run evidence.
- Produces: canonical C11 completion state and transition to C12.

- [ ] **Step 1: Create a dedicated closeout branch from the latest validated main**

Suggested branch:

```text
docs/construction-c11-closeout-status
```

- [ ] **Step 2: Update only the Construction STATUS header/evidence**

Set:

```text
PHASE=C11_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C12_RUNTIME_ACCEPTANCE
MANUAL_ACTION_REQUIRED=NO
```

Add C11 evidence fields for:

- implementation PR number;
- final implementation PR head SHA;
- implementation merge SHA;
- C11 workflow run IDs;
- Sonar/Governance run IDs;
- physical modlist SHA;
- registry file/content SHA;
- palette resolution SHA;
- Build IR content SHA;
- structural QA fingerprint/status;
- C8 preview/review/Visual QA fingerprints;
- `.schem` SHA;
- manifest SHA;
- post-merge gate summary.

Preserve all C0–C10 history byte-for-byte outside the intended C11 additions/header transition.

- [ ] **Step 3: Prove STATUS-only diff**

Compare closeout branch against its base and require exactly one changed file: `construction/STATUS.md`.

- [ ] **Step 4: Open closeout PR**

Title:

```text
docs(construction): close C11 postmerge validation
```

- [ ] **Step 5: Require all closeout gates green and merge with expected-head protection**

After merge, validate the exact new `main` SHA and all workflows triggered by the STATUS closeout.

C11 is not officially complete until this final post-merge validation is green.
