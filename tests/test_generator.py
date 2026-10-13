from pathlib import Path
import pytest
from react_clean_gen.config import write_default_project_config, load_project_config
from react_clean_gen.schema import load_module_spec
from react_clean_gen.platform_generator import generate_platform
from react_clean_gen.api_generator import generate_api_infrastructure
from react_clean_gen.feature_generator import generate_feature

ROOT = Path(__file__).parents[1]

def test_example_spec_parses():
    spec = load_module_spec(ROOT / "examples/customer.yml")
    assert spec.module == "customer"
    assert spec.api_path == "api/customers"
    assert spec.list_columns == ("firstName", "lastName", "email", "active")

def test_duplicate_field_rejected(tmp_path):
    p = tmp_path / "bad.yml"
    p.write_text("module: test\nentity:\n  name: Test\n  fields:\n    - {name: label, type: string}\n    - {name: label, type: string}\napiPath: /tests\n")
    with pytest.raises(ValueError, match="Duplicate field"):
        load_module_spec(p)

def test_feature_does_not_rewrite_platform(tmp_path):
    write_default_project_config(tmp_path)
    cfg = load_project_config(tmp_path)
    generate_platform(tmp_path, {"project_name":"test-app"})
    generate_api_infrastructure(tmp_path, cfg["api"])
    router = tmp_path / "src/app/router.tsx"
    before = router.read_text()
    generate_feature(tmp_path, load_module_spec(ROOT / "examples/customer.yml"), cfg)
    assert router.read_text() == before
    assert (tmp_path / "src/features/customer/infrastructure/customer-api.ts").exists()

def test_existing_files_are_not_overwritten_by_default(tmp_path):
    from react_clean_gen.writer import write_file
    p = tmp_path / "owned.ts"
    p.write_text("keep")
    _, status = write_file(tmp_path, "owned.ts", "replace")
    assert status == "skipped-existing"
    assert p.read_text() == "keep"
