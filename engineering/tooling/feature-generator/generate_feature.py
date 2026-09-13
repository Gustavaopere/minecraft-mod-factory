#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any


CORE_FEATURE_KINDS = (
    "block",
    "item",
    "block_entity",
    "menu",
    "network_payload",
    "recipe",
)
EXPECTED_TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}
MOD_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
JAVA_PACKAGE_RE = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*$")
CLASS_RE = re.compile(r"^[A-Z][A-Za-z0-9_]*$")
FEATURE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
SAFE_PATH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_$.-]+$")
ROLE_PATH_PREFIXES = {
    "feature_source": "src/main/java/",
    "registry": "src/main/java/",
    "datagen": "src/main/java/",
    "bootstrap": "src/main/java/",
    "generated_test": "src/test/java/",
}


class FeatureGeneratorError(ValueError):
    pass


class ConfirmationRequiredError(FeatureGeneratorError):
    pass


class StalePlanError(FeatureGeneratorError):
    pass


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_project_root(project_root: Path | str) -> Path:
    root = Path(project_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"project root must be a directory: {root}")
    return root


def _safe_relative_path(value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"path must be a safe relative path: {value!r}")
    parts = value.split("/")
    if any(
        part in {"", ".", ".."} or SAFE_PATH_SEGMENT_RE.fullmatch(part) is None
        for part in parts
    ):
        raise ValueError(f"path must be a safe relative path: {value!r}")
    return Path(*parts)


def _contained_path(root: Path, relative: str, *, must_exist: bool) -> Path:
    path = _safe_relative_path(relative)
    candidate = root.joinpath(*path.parts)
    if candidate.is_symlink():
        raise ValueError(f"symlink path is not allowed: {relative}")
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes authorized root: {relative}") from exc
    return resolved


def _workspace_input(workspace: Path, value: str, *, directory: bool) -> Path:
    resolved = _contained_path(workspace, value, must_exist=True)
    if directory and not resolved.is_dir():
        raise ValueError(f"workspace input must be a directory: {value}")
    if not directory and not resolved.is_file():
        raise ValueError(f"workspace input must be a file: {value}")
    return resolved


def _project_child(root: Path, relative: str) -> Path:
    return _contained_path(root, relative, must_exist=False)


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_nonempty_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be a non-empty string")
    return value


def _validate_request(request: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if request.get("schema_version") != 1:
        raise ValueError("feature request schema_version must be 1")
    target = _require_mapping(request.get("target"), "target")
    if target != EXPECTED_TARGET:
        raise ValueError(f"unsupported target; expected exact {EXPECTED_TARGET}")

    project = _require_mapping(request.get("project"), "project")
    mod_id = _require_nonempty_string(project, "mod_id", "project")
    java_package = _require_nonempty_string(project, "java_package", "project")
    main_class = _require_nonempty_string(project, "main_class", "project")
    if MOD_ID_RE.fullmatch(mod_id) is None:
        raise ValueError("project.mod_id is invalid")
    if JAVA_PACKAGE_RE.fullmatch(java_package) is None:
        raise ValueError("project.java_package is invalid")
    if CLASS_RE.fullmatch(main_class) is None:
        raise ValueError("project.main_class is invalid")

    raw_features = request.get("features")
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError("features must be a non-empty array")

    features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_classes: set[str] = set()
    for index, raw_feature in enumerate(raw_features):
        feature = _require_mapping(raw_feature, f"features[{index}]")
        kind = _require_nonempty_string(feature, "kind", f"features[{index}]")
        feature_id = _require_nonempty_string(feature, "id", f"features[{index}]")
        class_name = _require_nonempty_string(feature, "class_name", f"features[{index}]")
        if kind not in CORE_FEATURE_KINDS:
            raise ValueError(f"unsupported I8 core feature kind: {kind}")
        if FEATURE_ID_RE.fullmatch(feature_id) is None:
            raise ValueError(f"invalid feature id: {feature_id}")
        if CLASS_RE.fullmatch(class_name) is None:
            raise ValueError(f"invalid feature class_name: {class_name}")
        if feature_id in seen_ids:
            raise ValueError(f"duplicate feature id: {feature_id}")
        if class_name in seen_classes:
            raise ValueError(f"duplicate feature class_name: {class_name}")
        seen_ids.add(feature_id)
        seen_classes.add(class_name)
        features.append(dict(feature))

    block_ids = {feature["id"] for feature in features if feature["kind"] == "block"}
    for feature in features:
        if feature["kind"] != "block_entity":
            continue
        block_id = _require_nonempty_string(feature, "block_id", f"block_entity {feature['id']}")
        if FEATURE_ID_RE.fullmatch(block_id) is None:
            raise ValueError(f"invalid block_id for block entity {feature['id']}: {block_id}")
        if block_id not in block_ids:
            raise ValueError(
                f"block entity {feature['id']} requires block_id {block_id} in the same feature request"
            )
    return project, features


def _java_package_path(java_package: str) -> str:
    return java_package.replace(".", "/")


def _kind_package(kind: str) -> str:
    return kind


def _parse_gradle_properties(root: Path) -> dict[str, str]:
    properties_path = _project_child(root, "gradle.properties")
    if not properties_path.is_file():
        raise ValueError("target project is missing gradle.properties")
    properties: dict[str, str] = {}
    for raw_line in properties_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


def _validate_physical_project(root: Path, project: dict[str, Any]) -> Path:
    properties = _parse_gradle_properties(root)
    expected_properties = {
        "minecraft_version": EXPECTED_TARGET["minecraft"],
        "neo_version": EXPECTED_TARGET["neoforge"],
        "java_version": str(EXPECTED_TARGET["java"]),
        "mod_id": project["mod_id"],
    }
    for key, expected in expected_properties.items():
        if properties.get(key) != expected:
            raise ValueError(
                f"target project {key} mismatch: expected {expected!r}, got {properties.get(key)!r}"
            )

    java_package = project["java_package"]
    main_class = project["main_class"]
    package_path = _java_package_path(java_package)
    main_relative = f"src/main/java/{package_path}/{main_class}.java"
    main_path = _project_child(root, main_relative)
    if not main_path.is_file():
        raise ValueError(f"target project does not match requested main class: {main_relative}")
    source = main_path.read_text(encoding="utf-8")
    expected_markers = (
        f"package {java_package};",
        f"@Mod({main_class}.MOD_ID)",
        f'public static final String MOD_ID = "{project["mod_id"]}";',
    )
    if any(marker not in source for marker in expected_markers):
        raise ValueError("target main class identity does not match feature request")
    return main_path


def _existing_generated_feature_paths(root: Path, java_package: str) -> set[str]:
    package_path = _java_package_path(java_package)
    feature_root = _project_child(root, f"src/main/java/{package_path}/feature")
    if not feature_root.exists():
        return set()
    if feature_root.is_symlink() or not feature_root.is_dir():
        raise ValueError("generated feature root must be a regular directory")

    generated: set[str] = set()
    for kind in CORE_FEATURE_KINDS:
        kind_root = feature_root / kind
        if not kind_root.exists():
            continue
        if kind_root.is_symlink() or not kind_root.is_dir():
            raise ValueError(f"generated feature kind path must be a regular directory: {kind}")
        for candidate in sorted(kind_root.glob("*.java")):
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError(f"generated feature source must be a regular file: {candidate.name}")
            source = candidate.read_text(encoding="utf-8")
            marker = f'public static final String FEATURE_KIND = "{kind}";'
            if marker in source and 'public static final String ID = "' in source:
                generated.add(candidate.relative_to(root).as_posix())
    return generated


def _reject_non_cumulative_request(
    root: Path,
    java_package: str,
    features: list[dict[str, Any]],
) -> None:
    package_path = _java_package_path(java_package)
    requested_paths = {
        f"src/main/java/{package_path}/feature/{_kind_package(feature['kind'])}/{feature['class_name']}.java"
        for feature in features
    }
    missing = sorted(_existing_generated_feature_paths(root, java_package) - requested_paths)
    if missing:
        raise ValueError(
            "feature request is non-cumulative and would orphan existing generated features: "
            + ", ".join(missing)
        )


def _constant_name(feature_id: str) -> str:
    return feature_id.upper()


def _identity_fields(kind: str, feature_id: str) -> str:
    return (
        f"    public static final String FEATURE_KIND = \"{kind}\";\n"
        f"    public static final String ID = \"{feature_id}\";\n"
    )


def _block_source(package: str, class_name: str, feature_id: str) -> str:
    return (
        f"package {package};\n\n"
        "import net.minecraft.world.level.block.Block;\n"
        "import net.minecraft.world.level.block.state.BlockBehaviour;\n\n"
        f"public final class {class_name} extends Block {{\n"
        + _identity_fields("block", feature_id)
        + "\n"
        f"    public {class_name}(BlockBehaviour.Properties properties) {{\n"
        "        super(properties);\n"
        "    }\n"
        "}\n"
    )


def _item_source(package: str, class_name: str, feature_id: str) -> str:
    return (
        f"package {package};\n\n"
        "import net.minecraft.world.item.Item;\n\n"
        f"public final class {class_name} extends Item {{\n"
        + _identity_fields("item", feature_id)
        + "\n"
        f"    public {class_name}(Item.Properties properties) {{\n"
        "        super(properties);\n"
        "    }\n"
        "}\n"
    )


def _block_entity_source(java_package: str, package: str, class_name: str, feature_id: str) -> str:
    registry_constant = _constant_name(feature_id)
    return (
        f"package {package};\n\n"
        f"import {java_package}.registry.FactoryGeneratedRegistries;\n"
        "import net.minecraft.core.BlockPos;\n"
        "import net.minecraft.world.level.block.entity.BlockEntity;\n"
        "import net.minecraft.world.level.block.state.BlockState;\n\n"
        f"public final class {class_name} extends BlockEntity {{\n"
        + _identity_fields("block_entity", feature_id)
        + "\n"
        f"    public {class_name}(BlockPos pos, BlockState state) {{\n"
        f"        super(FactoryGeneratedRegistries.{registry_constant}.get(), pos, state);\n"
        "    }\n"
        "}\n"
    )


def _menu_source(java_package: str, package: str, class_name: str, feature_id: str) -> str:
    registry_constant = _constant_name(feature_id)
    return (
        f"package {package};\n\n"
        f"import {java_package}.registry.FactoryGeneratedRegistries;\n"
        "import net.minecraft.world.entity.player.Inventory;\n"
        "import net.minecraft.world.entity.player.Player;\n"
        "import net.minecraft.world.inventory.AbstractContainerMenu;\n"
        "import net.minecraft.world.item.ItemStack;\n\n"
        f"public final class {class_name} extends AbstractContainerMenu {{\n"
        + _identity_fields("menu", feature_id)
        + "\n"
        f"    public {class_name}(int containerId, Inventory playerInventory) {{\n"
        f"        super(FactoryGeneratedRegistries.{registry_constant}.get(), containerId);\n"
        "    }\n\n"
        "    @Override\n"
        "    public ItemStack quickMoveStack(Player player, int index) {\n"
        "        return ItemStack.EMPTY;\n"
        "    }\n\n"
        "    @Override\n"
        "    public boolean stillValid(Player player) {\n"
        "        return true;\n"
        "    }\n"
        "}\n"
    )


def _network_payload_source(package: str, class_name: str, feature_id: str, mod_id: str) -> str:
    return (
        f"package {package};\n\n"
        "import net.minecraft.network.protocol.common.custom.CustomPacketPayload;\n"
        "import net.minecraft.resources.ResourceLocation;\n\n"
        f"public record {class_name}() implements CustomPacketPayload {{\n"
        + _identity_fields("network_payload", feature_id)
        + "\n"
        f"    public static final CustomPacketPayload.Type<{class_name}> TYPE =\n"
        f"            new CustomPacketPayload.Type<>(ResourceLocation.fromNamespaceAndPath(\"{mod_id}\", ID));\n\n"
        "    @Override\n"
        "    public CustomPacketPayload.Type<? extends CustomPacketPayload> type() {\n"
        "        return TYPE;\n"
        "    }\n"
        "}\n"
    )


def _recipe_source(package: str, class_name: str, feature_id: str) -> str:
    return (
        f"package {package};\n\n"
        "import net.minecraft.core.HolderLookup;\n"
        "import net.minecraft.world.item.ItemStack;\n"
        "import net.minecraft.world.item.crafting.Recipe;\n"
        "import net.minecraft.world.item.crafting.RecipeSerializer;\n"
        "import net.minecraft.world.item.crafting.RecipeType;\n"
        "import net.minecraft.world.item.crafting.SingleRecipeInput;\n"
        "import net.minecraft.world.level.Level;\n\n"
        f"public final class {class_name} implements Recipe<SingleRecipeInput> {{\n"
        + _identity_fields("recipe", feature_id)
        + "\n"
        "    private final RecipeType<?> type;\n"
        "    private final RecipeSerializer<?> serializer;\n"
        "    private final ItemStack result;\n\n"
        f"    public {class_name}(RecipeType<?> type, RecipeSerializer<?> serializer, ItemStack result) {{\n"
        "        this.type = type;\n"
        "        this.serializer = serializer;\n"
        "        this.result = result.copy();\n"
        "    }\n\n"
        "    @Override\n"
        "    public boolean matches(SingleRecipeInput input, Level level) {\n"
        "        return false;\n"
        "    }\n\n"
        "    @Override\n"
        "    public ItemStack assemble(SingleRecipeInput input, HolderLookup.Provider registries) {\n"
        "        return this.result.copy();\n"
        "    }\n\n"
        "    @Override\n"
        "    public boolean canCraftInDimensions(int width, int height) {\n"
        "        return width * height >= 1;\n"
        "    }\n\n"
        "    @Override\n"
        "    public ItemStack getResultItem(HolderLookup.Provider registries) {\n"
        "        return this.result;\n"
        "    }\n\n"
        "    @Override\n"
        "    public RecipeSerializer<?> getSerializer() {\n"
        "        return this.serializer;\n"
        "    }\n\n"
        "    @Override\n"
        "    public RecipeType<?> getType() {\n"
        "        return this.type;\n"
        "    }\n"
        "}\n"
    )


def _feature_source(java_package: str, mod_id: str, feature: dict[str, Any]) -> str:
    kind = feature["kind"]
    feature_id = feature["id"]
    class_name = feature["class_name"]
    package = f"{java_package}.feature.{_kind_package(kind)}"
    if kind == "block":
        return _block_source(package, class_name, feature_id)
    if kind == "item":
        return _item_source(package, class_name, feature_id)
    if kind == "block_entity":
        return _block_entity_source(java_package, package, class_name, feature_id)
    if kind == "menu":
        return _menu_source(java_package, package, class_name, feature_id)
    if kind == "network_payload":
        return _network_payload_source(package, class_name, feature_id, mod_id)
    if kind == "recipe":
        return _recipe_source(package, class_name, feature_id)
    raise ValueError(f"unsupported I8 core feature kind: {kind}")


def _generated_test(java_package: str, feature: dict[str, Any]) -> str:
    kind = feature["kind"]
    feature_id = feature["id"]
    class_name = feature["class_name"]
    package = f"{java_package}.feature.{_kind_package(kind)}"
    test_class = f"{class_name}GeneratedTest"
    return (
        f"package {package};\n\n"
        "import org.junit.jupiter.api.Test;\n\n"
        "import static org.junit.jupiter.api.Assertions.assertEquals;\n\n"
        f"class {test_class} {{\n"
        "    @Test\n"
        "    void exposesGeneratedIdentity() {\n"
        f"        assertEquals(\"{kind}\", {class_name}.FEATURE_KIND);\n"
        f"        assertEquals(\"{feature_id}\", {class_name}.ID);\n"
        "    }\n"
        "}\n"
    )


def _feature_import(java_package: str, feature: dict[str, Any]) -> str:
    return f"import {java_package}.feature.{_kind_package(feature['kind'])}.{feature['class_name']};"


def _registry_source(java_package: str, main_class: str, features: list[dict[str, Any]]) -> str:
    by_kind = {
        kind: [feature for feature in features if feature["kind"] == kind]
        for kind in CORE_FEATURE_KINDS
    }
    feature_by_id = {feature["id"]: feature for feature in features}
    imports = {
        f"import {java_package}.{main_class};",
        "import java.util.function.Supplier;",
        "import net.neoforged.bus.api.IEventBus;",
        "import net.neoforged.neoforge.registries.DeferredRegister;",
    }
    for feature in features:
        if feature["kind"] != "network_payload":
            imports.add(_feature_import(java_package, feature))
    if by_kind["block"]:
        imports.add("import net.minecraft.world.level.block.state.BlockBehaviour;")
    if by_kind["item"]:
        imports.add("import net.minecraft.world.item.Item;")
    if by_kind["block_entity"] or by_kind["menu"] or by_kind["recipe"]:
        imports.add("import net.minecraft.core.registries.Registries;")
    if by_kind["block_entity"]:
        imports.add("import net.minecraft.world.level.block.entity.BlockEntityType;")
    if by_kind["menu"]:
        imports.add("import net.minecraft.world.flag.FeatureFlags;")
        imports.add("import net.minecraft.world.inventory.MenuType;")
    if by_kind["recipe"]:
        imports.add("import net.minecraft.world.item.crafting.RecipeType;")

    lines = [f"package {java_package}.registry;", "", *sorted(imports), "", "public final class FactoryGeneratedRegistries {"]
    registrar_names: list[str] = []
    if by_kind["block"]:
        lines.append(
            f"    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks({main_class}.MOD_ID);"
        )
        registrar_names.append("BLOCKS")
    if by_kind["item"]:
        lines.append(
            f"    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems({main_class}.MOD_ID);"
        )
        registrar_names.append("ITEMS")
    if by_kind["block_entity"]:
        lines.extend(
            [
                "    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITY_TYPES =",
                f"            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, {main_class}.MOD_ID);",
            ]
        )
        registrar_names.append("BLOCK_ENTITY_TYPES")
    if by_kind["menu"]:
        lines.extend(
            [
                "    public static final DeferredRegister<MenuType<?>> MENUS =",
                f"            DeferredRegister.create(Registries.MENU, {main_class}.MOD_ID);",
            ]
        )
        registrar_names.append("MENUS")
    if by_kind["recipe"]:
        lines.extend(
            [
                "    public static final DeferredRegister<RecipeType<?>> RECIPE_TYPES =",
                f"            DeferredRegister.create(Registries.RECIPE_TYPE, {main_class}.MOD_ID);",
            ]
        )
        registrar_names.append("RECIPE_TYPES")
    if registrar_names:
        lines.append("")

    for feature in by_kind["block"]:
        constant = _constant_name(feature["id"])
        lines.extend(
            [
                f"    public static final Supplier<{feature['class_name']}> {constant} = BLOCKS.registerBlock(",
                f"            \"{feature['id']}\", {feature['class_name']}::new, BlockBehaviour.Properties.of());",
                "",
            ]
        )
    for feature in by_kind["item"]:
        constant = _constant_name(feature["id"])
        lines.extend(
            [
                f"    public static final Supplier<{feature['class_name']}> {constant} = ITEMS.registerItem(",
                f"            \"{feature['id']}\", {feature['class_name']}::new, new Item.Properties());",
                "",
            ]
        )
    for feature in by_kind["block_entity"]:
        constant = _constant_name(feature["id"])
        block_constant = _constant_name(feature_by_id[feature["block_id"]]["id"])
        lines.extend(
            [
                f"    public static final Supplier<BlockEntityType<{feature['class_name']}>> {constant} =",
                f"            BLOCK_ENTITY_TYPES.register(\"{feature['id']}\", () -> BlockEntityType.Builder.of(",
                f"                    {feature['class_name']}::new, {block_constant}.get()).build(null));",
                "",
            ]
        )
    for feature in by_kind["menu"]:
        constant = _constant_name(feature["id"])
        lines.extend(
            [
                f"    public static final Supplier<MenuType<{feature['class_name']}>> {constant} =",
                f"            MENUS.register(\"{feature['id']}\", () -> new MenuType<>({feature['class_name']}::new, FeatureFlags.DEFAULT_FLAGS));",
                "",
            ]
        )
    for feature in by_kind["recipe"]:
        constant = _constant_name(feature["id"])
        lines.extend(
            [
                f"    public static final Supplier<RecipeType<{feature['class_name']}>> {constant} =",
                f"            RECIPE_TYPES.register(\"{feature['id']}\", RecipeType::simple);",
                "",
            ]
        )

    lines.append("    public static void register(IEventBus modBus) {")
    for registrar_name in registrar_names:
        lines.append(f"        {registrar_name}.register(modBus);")
    lines.extend(
        [
            "    }",
            "",
            "    private FactoryGeneratedRegistries() {",
            "    }",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _datagen_source(java_package: str, features: list[dict[str, Any]]) -> str:
    has_recipe = any(feature["kind"] == "recipe" for feature in features)
    lines = [f"package {java_package}.data;", ""]
    if has_recipe:
        lines.extend(
            [
                "import java.util.concurrent.CompletableFuture;",
                "import net.minecraft.core.HolderLookup;",
                "import net.minecraft.data.DataGenerator;",
                "import net.minecraft.data.PackOutput;",
                "import net.minecraft.data.recipes.RecipeOutput;",
                "import net.minecraft.data.recipes.RecipeProvider;",
                "import net.neoforged.neoforge.data.event.GatherDataEvent;",
                "",
                "public final class FactoryGeneratedData {",
                "    public static void gatherData(GatherDataEvent event) {",
                "        DataGenerator generator = event.getGenerator();",
                "        PackOutput output = generator.getPackOutput();",
                "        generator.addProvider(",
                "                event.includeServer(),",
                "                new FactoryGeneratedRecipeProvider(output, event.getLookupProvider())",
                "        );",
                "    }",
                "",
                "    public static final class FactoryGeneratedRecipeProvider extends RecipeProvider {",
                "        public FactoryGeneratedRecipeProvider(",
                "                PackOutput output,",
                "                CompletableFuture<HolderLookup.Provider> lookupProvider",
                "        ) {",
                "            super(output, lookupProvider);",
                "        }",
                "",
                "        @Override",
                "        protected void buildRecipes(RecipeOutput output) {",
                "        }",
                "    }",
                "",
                "    private FactoryGeneratedData() {",
                "    }",
                "}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "import net.neoforged.neoforge.data.event.GatherDataEvent;",
                "",
                "public final class FactoryGeneratedData {",
                "    public static void gatherData(GatherDataEvent event) {",
                "    }",
                "",
                "    private FactoryGeneratedData() {",
                "    }",
                "}",
                "",
            ]
        )
    return "\n".join(lines)


def _main_bootstrap_source(existing: str, java_package: str, main_class: str) -> str:
    registry_import = f"import {java_package}.registry.FactoryGeneratedRegistries;"
    datagen_import = f"import {java_package}.data.FactoryGeneratedData;"
    registry_call = "        FactoryGeneratedRegistries.register(modBus);"
    datagen_call = "        modBus.addListener(FactoryGeneratedData::gatherData);"
    markers = (registry_import, datagen_import, registry_call, datagen_call)
    present = [marker in existing for marker in markers]
    if all(present):
        return existing
    if any(present):
        raise ValueError("target main class contains partial I8 bootstrap wiring")

    package_marker = f"package {java_package};\n\n"
    constructor_marker = f"    public {main_class}(IEventBus modBus, ModContainer container) {{\n"
    if package_marker not in existing or constructor_marker not in existing:
        raise ValueError("target main class does not match canonical I3 bootstrap shape")
    updated = existing.replace(
        package_marker,
        package_marker + datagen_import + "\n" + registry_import + "\n",
        1,
    )
    return updated.replace(
        constructor_marker,
        constructor_marker + registry_call + "\n" + datagen_call + "\n",
        1,
    )


def _unified_diff(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def _planned_operation(root: Path, path: str, content: str, role: str) -> dict[str, Any]:
    destination = _project_child(root, path)
    if destination.exists():
        if not destination.is_file():
            raise ValueError(f"planned target exists but is not a file: {path}")
        before = destination.read_text(encoding="utf-8")
        if before == content:
            return {
                "action": "noop",
                "role": role,
                "path": path,
                "before_sha256": _sha256_text(before),
                "content": content,
                "diff": "",
                "requires_confirmation": False,
            }
        return {
            "action": "modify",
            "role": role,
            "path": path,
            "before_sha256": _sha256_text(before),
            "content": content,
            "diff": _unified_diff(path, before, content),
            "requires_confirmation": True,
        }
    return {
        "action": "create",
        "role": role,
        "path": path,
        "content": content,
        "diff": _unified_diff(path, "", content),
        "requires_confirmation": False,
    }


def _desired_file_specs(
    root: Path,
    project: dict[str, Any],
    features: list[dict[str, Any]],
) -> list[tuple[str, str, str]]:
    java_package = project["java_package"]
    mod_id = project["mod_id"]
    main_class = project["main_class"]
    package_path = _java_package_path(java_package)
    main_relative = f"src/main/java/{package_path}/{main_class}.java"
    main_path = _validate_physical_project(root, project)
    _reject_non_cumulative_request(root, java_package, features)

    specs: list[tuple[str, str, str]] = []
    for feature in features:
        kind = feature["kind"]
        class_name = feature["class_name"]
        relative_package = _kind_package(kind)
        source_path = f"src/main/java/{package_path}/feature/{relative_package}/{class_name}.java"
        test_path = f"src/test/java/{package_path}/feature/{relative_package}/{class_name}GeneratedTest.java"
        specs.append((source_path, _feature_source(java_package, mod_id, feature), "feature_source"))
        specs.append((test_path, _generated_test(java_package, feature), "generated_test"))

    registry_path = f"src/main/java/{package_path}/registry/FactoryGeneratedRegistries.java"
    specs.append((registry_path, _registry_source(java_package, main_class, features), "registry"))
    datagen_path = f"src/main/java/{package_path}/data/FactoryGeneratedData.java"
    specs.append((datagen_path, _datagen_source(java_package, features), "datagen"))
    main_content = main_path.read_text(encoding="utf-8")
    specs.append(
        (
            main_relative,
            _main_bootstrap_source(main_content, java_package, main_class),
            "bootstrap",
        )
    )
    return specs


def plan_feature_set(project_root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    root = _safe_project_root(project_root)
    project, features = _validate_request(request)
    operations = [
        _planned_operation(root, path, content, role)
        for path, content, role in _desired_file_specs(root, project, features)
    ]
    operations.sort(key=lambda operation: (operation["path"], operation["role"], operation["action"]))
    return {
        "schema_version": 1,
        "feature_kinds": [feature["kind"] for feature in features],
        "conflicts": [],
        "operations": operations,
    }


def _preflight_operation(root: Path, operation: dict[str, Any], *, confirm_modified: bool) -> tuple[Path, str]:
    action = operation.get("action")
    role = operation.get("role")
    path_value = operation.get("path")
    content = operation.get("content")
    if action not in {"create", "modify", "noop"}:
        raise ValueError(f"unknown plan action: {action}")
    if not isinstance(role, str) or role not in ROLE_PATH_PREFIXES:
        raise ValueError(f"unknown plan role: {role}")
    if not isinstance(path_value, str) or not isinstance(content, str):
        raise ValueError("plan operation requires string path and content")
    if not path_value.startswith(ROLE_PATH_PREFIXES[role]) or not path_value.endswith(".java"):
        raise ValueError(f"plan role {role} cannot target path: {path_value}")
    destination = _project_child(root, path_value)

    if action == "create":
        if destination.exists():
            raise StalePlanError(f"create target appeared after planning: {path_value}")
        return destination, content
    if not destination.is_file():
        raise StalePlanError(f"planned existing file is missing: {path_value}")
    current = destination.read_text(encoding="utf-8")
    expected_hash = operation.get("before_sha256")
    if not isinstance(expected_hash, str) or _sha256_text(current) != expected_hash:
        raise StalePlanError(f"planned file changed after planning: {path_value}")
    if action == "noop":
        return destination, current
    diff = operation.get("diff")
    if not isinstance(diff, str) or not diff:
        raise ValueError("modify operation requires a non-empty diff")
    if not confirm_modified:
        raise ConfirmationRequiredError(f"modified file requires explicit confirmation; diff follows:\n{diff}")
    return destination, content


def apply_feature_set(
    project_root: Path | str,
    request: dict[str, Any],
    *,
    confirm_modified: bool = False,
) -> list[Path]:
    root = _safe_project_root(project_root)
    project, features = _validate_request(request)
    specs = _desired_file_specs(root, project, features)

    prepared: list[tuple[dict[str, Any], Path, str]] = []
    seen: set[Path] = set()
    for path, content, role in specs:
        operation = _planned_operation(root, path, content, role)
        destination, prepared_content = _preflight_operation(
            root,
            operation,
            confirm_modified=confirm_modified,
        )
        if destination in seen:
            raise ValueError(f"duplicate planned destination: {destination.relative_to(root)}")
        seen.add(destination)
        prepared.append((operation, destination, prepared_content))

    written: list[Path] = []
    for operation, destination, content in prepared:
        if operation["action"] == "noop":
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
        written.append(destination)
    return written


def load_request(workspace: Path, relative_path: str) -> dict[str, Any]:
    request_path = _workspace_input(workspace, relative_path, directory=False)
    value = json.loads(request_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("feature request root must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan and apply deterministic I8 feature skeleton generation.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-modified", action="store_true")
    args = parser.parse_args()

    workspace = Path.cwd().resolve(strict=True)
    project_root = _workspace_input(workspace, args.project, directory=True)
    request = load_request(workspace, args.request)
    plan = plan_feature_set(project_root, request)
    print(json.dumps(plan, indent=2, sort_keys=True))
    if args.apply:
        apply_feature_set(project_root, request, confirm_modified=args.confirm_modified)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
