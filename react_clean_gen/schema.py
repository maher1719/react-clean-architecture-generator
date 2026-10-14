"""YAML schema parsing and validation; no template dependencies."""
import re
from dataclasses import dataclass
from pathlib import Path
import yaml
from .global_config import SUPPORTED_FIELD_TYPES, SUPPORTED_OPERATIONS

@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str
    required: bool = False
    label: str | None = None
    sortable: bool = False
    filterable: bool = False
    read_only: bool = False

@dataclass(frozen=True)
class ApiResponseSpec:
    collection_path: str = "items"
    item_path: str = ""
    item_response_path: str = ""
    total_path: str = "totalItems"
    page_path: str = "page"
    page_size_path: str = "pageSize"
    page_param: str = "page"
    page_size_param: str = "limit"

@dataclass(frozen=True)
class RelationSpec:
    field: str
    name: str
    kind: str
    label: str
    resource: str
    label_field: str
    value_field: str = "id"
    required: bool = False
    nullable: bool = False
    initial_value_field: str = ""
    collection_path: str = "data"
    item_path: str = "props"
    item_response_path: str = "props"
    search_param: str = "search"
    page_param: str = "page"
    page_size_param: str = "limit"
    page_size: int = 50

@dataclass(frozen=True)
class ModuleSpec:
    module: str
    entity_name: str
    api_path: str
    route: str
    title: str
    fields: tuple[FieldSpec, ...]
    operations: tuple[str, ...]
    list_columns: tuple[str, ...]
    api_response: ApiResponseSpec
    relations: tuple[RelationSpec, ...] = ()
    list_search_enabled: bool = True

def required_string(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where} must be a non-empty string.")
    return value.strip()

def path_string(value, where, allow_empty=False):
    if allow_empty and value == "":
        return ""
    value = required_string(value, where)
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part) for part in value.split(".")):
        raise ValueError(f"{where} must be a dot-separated property path, e.g. data or data.props.")
    return value

def load_module_spec(path: Path) -> ModuleSpec:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Module YAML root must be a mapping.")
    module = required_string(raw.get("module"), "module")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", module):
        raise ValueError("module must be lowercase kebab-case.")
    entity = raw.get("entity")
    if not isinstance(entity, dict):
        raise ValueError("entity must be a mapping.")
    entity_name = required_string(entity.get("name"), "entity.name")
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", entity_name):
        raise ValueError("entity.name must be a PascalCase TypeScript identifier.")

    api_cfg = raw.get("api", {})
    if api_cfg is None: api_cfg = {}
    if not isinstance(api_cfg, dict):
        raise ValueError("api must be a mapping.")
    raw_api_path = api_cfg.get("path", raw.get("apiPath"))
    api_path = required_string(raw_api_path, "api.path (or legacy apiPath)").strip("/")
    if not api_path or "?" in api_path or "#" in api_path:
        raise ValueError("api.path must be a relative API path without query or fragment.")

    response_cfg = api_cfg.get("response", {})
    pagination_cfg = api_cfg.get("pagination", {})
    if not isinstance(response_cfg, dict): raise ValueError("api.response must be a mapping.")
    if not isinstance(pagination_cfg, dict): raise ValueError("api.pagination must be a mapping.")
    response = ApiResponseSpec(
        collection_path=path_string(response_cfg.get("collectionPath", "items"), "api.response.collectionPath"),
        item_path=path_string(response_cfg.get("itemPath", ""), "api.response.itemPath", allow_empty=True),
        item_response_path=path_string(response_cfg.get("itemResponsePath", response_cfg.get("itemPath", "")), "api.response.itemResponsePath", allow_empty=True),
        total_path=path_string(response_cfg.get("totalPath", "totalItems"), "api.response.totalPath"),
        page_path=path_string(response_cfg.get("pagePath", "page"), "api.response.pagePath"),
        page_size_path=path_string(response_cfg.get("pageSizePath", "pageSize"), "api.response.pageSizePath"),
        page_param=required_string(pagination_cfg.get("pageParam", "page"), "api.pagination.pageParam"),
        page_size_param=required_string(pagination_cfg.get("pageSizeParam", "pageSize"), "api.pagination.pageSizeParam"),
    )
    for param_name, param in (("pageParam", response.page_param), ("pageSizeParam", response.page_size_param)):
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", param):
            raise ValueError(f"api.pagination.{param_name} must be a simple query parameter name.")

    ui = raw.get("ui", {})
    if not isinstance(ui, dict): raise ValueError("ui must be a mapping.")
    route = required_string(ui.get("route", "/" + module), "ui.route")
    if not route.startswith("/") or route.startswith("//"):
        raise ValueError("ui.route must start with exactly one '/'.")
    title = required_string(ui.get("title", entity_name), "ui.title")
    raw_fields = entity.get("fields")
    if not isinstance(raw_fields, list) or not raw_fields:
        raise ValueError("entity.fields must be a non-empty list.")
    fields, names = [], set()
    for i, item in enumerate(raw_fields):
        where = f"entity.fields[{i}]"
        if not isinstance(item, dict): raise ValueError(f"{where} must be a mapping.")
        name = required_string(item.get("name"), where + ".name")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name):
            raise ValueError(f"{where}.name must be a camelCase TypeScript identifier.")
        if name in names: raise ValueError(f"Duplicate field name: {name}")
        names.add(name)
        typ = required_string(item.get("type"), where + ".type").lower()
        if typ not in SUPPORTED_FIELD_TYPES: raise ValueError(f"Unsupported type '{typ}' for {name}.")
        bools = [item.get(k, False) for k in ("required", "sortable", "filterable", "readOnly")]
        if not all(isinstance(v, bool) for v in bools):
            raise ValueError(f"{where}: required/sortable/filterable/readOnly must be booleans.")
        label = item.get("label")
        if label is not None and not isinstance(label, str): raise ValueError(f"{where}.label must be a string.")
        fields.append(FieldSpec(name, typ, bools[0], label, bools[1], bools[2], bools[3]))
    raw_ops = raw.get("operations", ["list", "get", "create", "patch", "delete"])
    if not isinstance(raw_ops, list) or not raw_ops or not all(isinstance(x, str) for x in raw_ops):
        raise ValueError("operations must be a non-empty list of strings.")
    operations = tuple(dict.fromkeys(x.lower() for x in raw_ops))
    unknown = set(operations) - SUPPORTED_OPERATIONS
    if unknown: raise ValueError("Unsupported operations: " + ", ".join(sorted(unknown)))
    list_cfg = ui.get("list", {})
    if not isinstance(list_cfg, dict): raise ValueError("ui.list must be a mapping.")
    columns = list_cfg.get("columns", [f.name for f in fields])
    if not isinstance(columns, list) or not columns or any(not isinstance(x, str) or x not in names for x in columns):
        raise ValueError("ui.list.columns must contain valid entity field names.")
    search_enabled = list_cfg.get("search", True)
    if not isinstance(search_enabled, bool):
        raise ValueError("ui.list.search must be a boolean.")

    form_cfg = ui.get("form", {}) or {}
    if not isinstance(form_cfg, dict): raise ValueError("ui.form must be a mapping.")
    raw_relations = form_cfg.get("relations", [])
    if not isinstance(raw_relations, list): raise ValueError("ui.form.relations must be a list.")
    relations, relation_fields = [], set()
    for i, rel in enumerate(raw_relations):
        where = f"ui.form.relations[{i}]"
        if not isinstance(rel, dict): raise ValueError(f"{where} must be a mapping.")
        field = required_string(rel.get("field"), where + ".field")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", field): raise ValueError(f"{where}.field must be a camelCase identifier.")
        if field in relation_fields: raise ValueError(f"Duplicate relation payload field: {field}")
        relation_fields.add(field)
        name = required_string(rel.get("name", field), where + ".name")
        kind = required_string(rel.get("kind"), where + ".kind").lower()
        if kind not in {"single", "multiple"}: raise ValueError(f"{where}.kind must be 'single' or 'multiple'.")
        resource = required_string(rel.get("resource"), where + ".resource")
        if not resource.startswith("/") or resource.startswith("//") or "?" in resource or "#" in resource:
            raise ValueError(f"{where}.resource must be an absolute API path without query or fragment.")
        label = required_string(rel.get("label", name), where + ".label")
        label_field = required_string(rel.get("labelField"), where + ".labelField")
        value_field = required_string(rel.get("valueField", "id"), where + ".valueField")
        required = rel.get("required", False)
        nullable = rel.get("nullable", False)
        if not isinstance(required, bool) or not isinstance(nullable, bool): raise ValueError(f"{where}: required and nullable must be booleans.")
        response_rel = rel.get("response", {}) or {}
        pagination_rel = rel.get("pagination", {}) or {}
        if not isinstance(response_rel, dict) or not isinstance(pagination_rel, dict): raise ValueError(f"{where}: response and pagination must be mappings.")
        collection_path = path_string(response_rel.get("collectionPath", "data"), where + ".response.collectionPath")
        item_path = path_string(response_rel.get("itemPath", "props"), where + ".response.itemPath", allow_empty=True)
        item_response_path = path_string(response_rel.get("itemResponsePath", item_path), where + ".response.itemResponsePath", allow_empty=True)
        initial_value_field = required_string(rel.get("initialValueField", field), where + ".initialValueField")
        search_param = required_string(rel.get("searchParam", "search"), where + ".searchParam")
        page_param = required_string(pagination_rel.get("pageParam", "page"), where + ".pagination.pageParam")
        page_size_param = required_string(pagination_rel.get("pageSizeParam", "limit"), where + ".pagination.pageSizeParam")
        page_size = pagination_rel.get("pageSize", 50)
        if not isinstance(page_size, int) or isinstance(page_size, bool) or page_size < 1 or page_size > 500:
            raise ValueError(f"{where}.pagination.pageSize must be an integer from 1 to 500.")
        for pname, pvalue in (("searchParam", search_param), ("pageParam", page_param), ("pageSizeParam", page_size_param)):
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", pvalue): raise ValueError(f"{where}.{pname} must be a simple query parameter name.")
        relations.append(RelationSpec(field, name, kind, label, resource, label_field, value_field, required, nullable,
                                      initial_value_field, collection_path, item_path, item_response_path,
                                      search_param, page_param, page_size_param, page_size))
    return ModuleSpec(module, entity_name, api_path, route, title, tuple(fields), operations,
                      tuple(dict.fromkeys(columns)), response, tuple(relations), search_enabled)
