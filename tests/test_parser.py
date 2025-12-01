import unittest
from pathlib import Path

from cellcli.parser import parse_cell_spec
from cellcli.errors import CellSpecError


class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        # Project root is two levels up from this file
        self.root = Path(__file__).resolve().parents[1]
        self.spec_path = self.root / "examples" / "cell-spec.md"

    def test_parse_valid_spec(self) -> None:
        cell = parse_cell_spec(self.spec_path)

        self.assertEqual(cell.cell_name, "icc-01")
        self.assertEqual(cell.realm_name, "dev-east")
        self.assertEqual(cell.region, "us-east-2")

        # Layers
        names = {layer.name for layer in cell.layers}
        self.assertSetEqual(names, {"kernel", "platform", "gateway", "apps"})

        # Database
        self.assertEqual(cell.database.instance_class, "db.t3.small")
        self.assertEqual(cell.database.storage_gb, 20)

        # Cache
        self.assertEqual(cell.cache.node_type, "cache.t3.micro")
        self.assertEqual(cell.cache.nodes, 1)

    def test_missing_file_raises(self) -> None:
        bad_path = self.root / "examples" / "does-not-exist.md"
        with self.assertRaises(CellSpecError):
            parse_cell_spec(bad_path)


if __name__ == "__main__":
    unittest.main()
