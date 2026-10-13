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

def required_string(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where} must be a non-empty string.")
    return value.strip()

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
    api_path = required_string(raw.get("apiPath"), "apiPath").strip("/")
    if not api_path or "?" in api_path or "#" in api_path:
        raise ValueError("apiPath must be a relative API path without query or fragment.")
    ui = raw.get("ui", {})
    if not isinstance(ui, dict):
        raise ValueError("ui must be a mapping.")
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
        if not isinstance(item, dict):
            raise ValueError(f"{where} must be a mapping.")
        name = required_string(item.get("name"), where + ".name")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name):
            raise ValueError(f"{where}.name must be a camelCase TypeScript identifier.")
        if name in names:
            raise ValueError(f"Duplicate field name: {name}")
        names.add(name)
        typ = required_string(item.get("type"), where + ".type").lower()
        if typ not in SUPPORTED_FIELD_TYPES:
            raise ValueError(f"Unsupported type '{typ}' for {name}.")
        bools = [item.get(k, False) for k in ("required", "sortable", "filterable")]
        if not all(isinstance(v, bool) for v in bools):
            raise ValueError(f"{where}: required/sortable/filterable must be booleans.")
        fields.append(FieldSpec(name, typ, bools[0], item.get("label"), bools[1], bools[2]))
    raw_ops = raw.get("operations", ["list", "get", "create", "patch", "delete"])
    if not isinstance(raw_ops, list) or not raw_ops or not all(isinstance(x, str) for x in raw_ops):
        raise ValueError("operations must be a non-empty list of strings.")
    operations = tuple(dict.fromkeys(x.lower() for x in raw_ops))
    unknown = set(operations) - SUPPORTED_OPERATIONS
    if unknown:
        raise ValueError("Unsupported operations: " + ", ".join(sorted(unknown)))
    list_cfg = ui.get("list", {})
    if not isinstance(list_cfg, dict):
        raise ValueError("ui.list must be a mapping.")
    columns = list_cfg.get("columns", [f.name for f in fields])
    if not isinstance(columns, list) or not columns or any(not isinstance(x, str) or x not in names for x in columns):
        raise ValueError("ui.list.columns must contain valid entity field names.")
    return ModuleSpec(module, entity_name, api_path, route, title, tuple(fields), operations, tuple(dict.fromkeys(columns)))
