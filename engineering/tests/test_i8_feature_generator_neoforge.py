import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "engineering/tooling/feature-generator/generate_feature.py"
GOLDEN = ROOT / "engineering/tests/golden/i3-golden-mod"
REQUEST_FIXTURE = ROOT / "engineering/tests/fixtures/i8-feature-set.json"
PACKAGE_PATH = Path("dev/example/i3golden")


def load_generator():
    spec = importlib.util.spec_from_file_location("i8_generate_feature", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_request():
    return json.loads(REQUEST_FIXTURE.read_text(encoding="utf-8"))


def copy_golden(target: Path) -> Path:
    shutil.copytree(GOLDEN, target)
    return target


class I8NeoForgeSkeletonContractTest(unittest.TestCase):
    def setUp(self):
        self.module = load_generator()

    def generate(self, project: Path) -> None:
        plan = self.module.plan_feature_set(project, load_request())
        self.module.apply_plan(project, plan, confirm_modified=True)

    def read_source(self, project: Path, kind: str, class_name: str) -> str:
        path = project / "src/main/java" / PACKAGE_PATH / "feature" / kind / f"{class_name}.java"
        self.assertTrue(path.is_file(), f"missing generated source: {path}")
        return path.read_text(encoding="utf-8")

    def test_block_skeleton_uses_real_minecraft_block_base_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = self.read_source(project, "block", "CopperMachineBlock")
        self.assertIn("extends Block", source)
        self.assertIn("BlockBehaviour.Properties", source)
        self.assertIn("super(properties);", source)

    def test_item_skeleton_uses_real_minecraft_item_base_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = self.read_source(project, "item", "CopperGearItem")
        self.assertIn("extends Item", source)
        self.assertIn("Item.Properties", source)
        self.assertIn("super(properties);", source)

    def test_block_entity_skeleton_uses_real_block_entity_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = self.read_source(project, "block_entity", "CopperMachineBlockEntity")
        self.assertIn("extends BlockEntity", source)
        self.assertIn("BlockPos pos", source)
        self.assertIn("BlockState state", source)
        self.assertIn("super(FactoryGeneratedRegistries.COPPER_MACHINE_ENTITY.get(), pos, state);", source)

    def test_menu_skeleton_uses_real_container_menu_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = self.read_source(project, "menu", "CopperMachineMenu")
        self.assertIn("extends AbstractContainerMenu", source)
        self.assertIn("Inventory playerInventory", source)
        self.assertIn("FactoryGeneratedRegistries.COPPER_MACHINE_MENU.get()", source)
        self.assertIn("quickMoveStack", source)
        self.assertIn("stillValid", source)

    def test_network_payload_skeleton_uses_custom_packet_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = self.read_source(project, "network_payload", "MachineActionPayload")
        self.assertIn("implements CustomPacketPayload", source)
        self.assertIn("CustomPacketPayload.Type<MachineActionPayload>", source)
        self.assertIn("ResourceLocation.fromNamespaceAndPath", source)
        self.assertIn("type()", source)

    def test_recipe_skeleton_uses_real_recipe_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = self.read_source(project, "recipe", "CopperProcessingRecipe")
        self.assertIn("implements Recipe<SingleRecipeInput>", source)
        self.assertIn("matches(SingleRecipeInput input, Level level)", source)
        self.assertIn("assemble(SingleRecipeInput input, HolderLookup.Provider registries)", source)
        self.assertIn("getSerializer()", source)
        self.assertIn("getType()", source)

    def test_registry_surface_uses_neoforge_deferred_registers_for_generated_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = (project / "src/main/java" / PACKAGE_PATH / "registry/FactoryGeneratedRegistries.java").read_text(encoding="utf-8")

        self.assertIn("DeferredRegister.createBlocks(I3GoldenMod.MOD_ID)", source)
        self.assertIn("DeferredRegister.createItems(I3GoldenMod.MOD_ID)", source)
        self.assertIn("DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, I3GoldenMod.MOD_ID)", source)
        self.assertIn("DeferredRegister.create(Registries.MENU, I3GoldenMod.MOD_ID)", source)
        self.assertIn("DeferredRegister.create(Registries.RECIPE_TYPE, I3GoldenMod.MOD_ID)", source)
        self.assertIn('BLOCKS.registerBlock("copper_machine", CopperMachineBlock::new', source)
        self.assertIn('ITEMS.registerItem("copper_gear", CopperGearItem::new', source)
        self.assertIn("CopperMachineBlockEntity::new", source)
        self.assertIn("new MenuType<>(CopperMachineMenu::new, FeatureFlags.DEFAULT_FLAGS)", source)
        self.assertIn("RecipeType::simple", source)
        self.assertIn("public static void register(IEventBus modBus)", source)
        self.assertIn("BLOCKS.register(modBus);", source)
        self.assertIn("ITEMS.register(modBus);", source)
        self.assertIn("BLOCK_ENTITY_TYPES.register(modBus);", source)
        self.assertIn("MENUS.register(modBus);", source)
        self.assertIn("RECIPE_TYPES.register(modBus);", source)

    def test_datagen_surface_registers_real_recipe_provider_from_gather_data_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.generate(project)
            source = (project / "src/main/java" / PACKAGE_PATH / "data/FactoryGeneratedData.java").read_text(encoding="utf-8")

        self.assertIn("GatherDataEvent", source)
        self.assertIn("extends RecipeProvider", source)
        self.assertIn("buildRecipes(RecipeOutput output)", source)
        self.assertIn("DataGenerator generator = event.getGenerator();", source)
        self.assertIn("generator.addProvider(", source)
        self.assertIn("event.includeServer()", source)
        self.assertIn("new FactoryGeneratedRecipeProvider(output, event.getLookupProvider())", source)


if __name__ == "__main__":
    unittest.main()
