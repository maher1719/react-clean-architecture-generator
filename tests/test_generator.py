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
    assert (tmp_path / "src/shared/ui/DataTable.tsx").exists()
    assert (tmp_path / "src/vite-env.d.ts").exists()
    assert (tmp_path / "src/shared/api/response-normalizer.ts").exists()
    assert (tmp_path / "src/features/customer/infrastructure/customer-api.ts").exists()

def test_existing_files_are_not_overwritten_by_default(tmp_path):
    from react_clean_gen.writer import write_file
    p = tmp_path / "owned.ts"
    p.write_text("keep")
    _, status = write_file(tmp_path, "owned.ts", "replace")
    assert status == "skipped-existing"
    assert p.read_text() == "keep"

def test_user_spec_captures_props_wrapper_and_limit_param():
    spec = load_module_spec(ROOT / "examples/user.yml")
    assert spec.api_path == "api/users"
    assert spec.api_response.collection_path == "data"
    assert spec.api_response.item_path == "props"
    assert spec.api_response.page_size_path == "limit"
    assert spec.api_response.page_size_param == "limit"


def test_user_feature_generates_normalization_table_and_pagination(tmp_path):
    write_default_project_config(tmp_path)
    cfg = load_project_config(tmp_path)
    spec = load_module_spec(ROOT / "examples/user.yml")
    generate_feature(tmp_path, spec, cfg)
    api = (tmp_path / "src/features/user/infrastructure/user-api.ts").read_text()
    renderer = (tmp_path / "src/features/user/presentation/user-list-renderer.tsx").read_text()
    model = (tmp_path / "src/features/user/application/use-user-list-model.ts").read_text()
    entity = (tmp_path / "src/features/user/domain/user.ts").read_text()
    assert 'itemPath: "props"' in api
    assert 'p.set("limit", String(query.pageSize))' in api
    assert "Previous" in renderer and "Next" in renderer
    assert "Loading users" in renderer and "No users found" in renderer
    assert "controller.abort()" in model
    assert 'Pick<User, "name" | "email">' in entity


def test_update_operation_and_filterable_fields_generate_crud(tmp_path):
    write_default_project_config(tmp_path)
    cfg = load_project_config(tmp_path)
    spec_path = tmp_path / "posts.yml"
    spec_path.write_text("""module: posts
entity:
  name: Post
  fields:
    - {name: title, type: string, required: true, filterable: true}
    - {name: published, type: boolean, filterable: true}
operations: [list, get, create, update, delete]
api:
  path: /api/posts
  response: {collectionPath: data, itemPath: props, totalPath: total, pagePath: page, pageSizePath: limit}
  pagination: {pageParam: page, pageSizeParam: limit}
ui:
  route: /posts
  title: Posts
  list: {columns: [title, published], search: true}
""", encoding="utf-8")
    spec = load_module_spec(spec_path)
    generate_feature(tmp_path, spec, cfg)
    route = (tmp_path / "src/features/posts/presentation/posts-route.tsx").read_text()
    form = (tmp_path / "src/features/posts/presentation/posts-form.tsx").read_text()
    renderer = (tmp_path / "src/features/posts/presentation/posts-list-renderer.tsx").read_text()
    api = (tmp_path / "src/features/posts/infrastructure/posts-api.ts").read_text()
    assert "postsApi.update" in route
    assert "postsApi.delete" in route
    assert "Create post" in route
    assert 'type="checkbox"' in form
    assert "filter[" in api
    assert "Apply" in renderer and "Clear" in renderer


def test_relation_selects_generate_single_multiple_and_hydration(tmp_path):
    write_default_project_config(tmp_path)
    cfg = load_project_config(tmp_path)
    spec = load_module_spec(ROOT / "examples/posts.yml")
    assert [(r.field, r.kind) for r in spec.relations] == [
        ("authorId", "single"), ("coverImageId", "single"),
        ("tagIds", "multiple"), ("coAuthorIds", "multiple")]
    generate_feature(tmp_path, spec, cfg)
    form = (tmp_path / "src/features/posts/presentation/posts-form.tsx").read_text()
    api = (tmp_path / "src/features/posts/infrastructure/posts-api.ts").read_text()
    entity = (tmp_path / "src/features/posts/domain/posts.ts").read_text()
    route = (tmp_path / "src/features/posts/presentation/posts-route.tsx").read_text()
    selector = (tmp_path / "src/shared/ui/RelationSelect.tsx").read_text()
    assert form.count("<RelationSelect") == 4
    assert 'kind="multiple"' in form and 'kind="single"' in form
    assert 'payload["tagIds"]' in form and 'payload["coAuthorIds"]' in form
    assert "normalizeItemResponse<Post>" in api
    assert 'tagIds?: string[]' in entity and 'coAuthorIds?: string[]' in entity
    assert "Loading record and relationships" in route
    assert "encodeURIComponent(selected)" in selector


def test_invalid_relation_kind_rejected(tmp_path):
    p = tmp_path / "bad-relation.yml"
    p.write_text("""module: posts
entity:
  name: Post
  fields: [{name: title, type: string}]
apiPath: /posts
ui:
  form:
    relations:
      - {field: authorId, kind: many-to-one, resource: /users, labelField: name}
""", encoding="utf-8")
    with pytest.raises(ValueError, match="kind must be 'single' or 'multiple'"):
        load_module_spec(p)
