import unittest
from pathlib import Path

from cellcli.parser import parse_cell_spec
from cellcli.generators import generate_tfvars, generate_env


class TestGenerators(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        spec_path = root / "examples" / "cell-spec.md"
        self.cell = parse_cell_spec(spec_path)

    def test_generate_tfvars_contains_core_fields(self) -> None:
        content = generate_tfvars(self.cell)

        self.assertIn('cell_name  = "icc-01"', content)
        self.assertIn('realm_name = "dev-east"', content)
        self.assertIn('region     = "us-east-2"', content)

        self.assertIn("kernel_cpu    = 256", content)
        self.assertIn("platform_memory = 1024", content)
        self.assertIn('db_instance_class = "db.t3.small"', content)
        self.assertIn("db_storage_gb     = 20", content)

    def test_generate_env_contains_core_fields(self) -> None:
        content = generate_env(self.cell)

        self.assertIn("CELL_NAME=icc-01", content)
        self.assertIn("REALM_NAME=dev-east", content)
        self.assertIn("REGION=us-east-2", content)

        self.assertIn("KERNEL_CPU=256", content)
        self.assertIn("APPS_MEMORY_MB=1024", content)
        self.assertIn("DB_INSTANCE_CLASS=db.t3.small", content)
        self.assertIn("CACHE_NODES=1", content)


if __name__ == "__main__":
    unittest.main()
