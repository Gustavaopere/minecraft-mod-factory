import contextlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = ROOT / "engineering/tooling/multiblock-foundation/materialize_i10.py"

EXPECTED_ITEM_MODELS = {
    "multiblock_controller.json": "i10_multiblock:block/controller_unformed",
    "multiblock_casing.json": "i10_multiblock:block/casing",
    "multiblock_io_port.json": "i10_multiblock:block/io_port_unformed",
}

EXPECTED_MODEL_RENDER_BLOCKS = (
    "MultiblockControllerBlock.java",
    "MultiblockPortBlock.java",
)


def load_module(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"I10 RED: required module is missing: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class I10ClientResourceRegression(unittest.TestCase):
    def test_materialized_block_items_have_item_models(self):
        materializer = load_module(MATERIALIZER, "i10_client_resource_materializer")
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with contextlib.chdir(workspace):
                generated = materializer.materialize_i10("generated")

            item_model_root = generated / "src/main/resources/assets/i10_multiblock/models/item"
            for filename, expected_parent in EXPECTED_ITEM_MODELS.items():
                with self.subTest(filename=filename):
                    path = item_model_root / filename
                    self.assertTrue(
                        path.is_file(),
                        f"I10 RED: materialized BlockItem model is missing: {filename}",
                    )
                    self.assertEqual(
                        {"parent": expected_parent},
                        json.loads(path.read_text(encoding="utf-8")),
                    )

    def test_materialized_block_entities_render_their_block_models(self):
        materializer = load_module(MATERIALIZER, "i10_client_render_shape_materializer")
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with contextlib.chdir(workspace):
                generated = materializer.materialize_i10("generated")

            source_root = (
                generated
                / "src/main/java/dev/example/i10multiblock/multiblock"
            )
            for filename in EXPECTED_MODEL_RENDER_BLOCKS:
                with self.subTest(filename=filename):
                    source = (source_root / filename).read_text(encoding="utf-8")
                    self.assertIn(
                        "import net.minecraft.world.level.block.RenderShape;",
                        source,
                        f"I10 RED: {filename} must import RenderShape for model rendering",
                    )
                    self.assertIn(
                        "protected RenderShape getRenderShape(BlockState state)",
                        source,
                        f"I10 RED: {filename} must override getRenderShape",
                    )
                    self.assertIn(
                        "return RenderShape.MODEL;",
                        source,
                        f"I10 RED: {filename} must render its blockstate model",
                    )


if __name__ == "__main__":
    unittest.main()
