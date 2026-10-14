import re
from pathlib import Path
from .global_config import SUPPORTED_FIELD_TYPES
from .schema import ModuleSpec
from .writer import render, write_file

def pascal_case(value):
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[-_ ]+", value) if part)

def camel_case(value):
    value = pascal_case(value)
    return value[:1].lower() + value[1:]

def generate_feature(target: Path, spec: ModuleSpec, config: dict, force=False):
    pascal, camel = pascal_case(spec.module), camel_case(spec.module)
    fields = [{"name": f.name, "type": next(("string[]" if r.kind == "multiple" else ("string | null" if r.nullable else "string") for r in spec.relations if r.field == f.name), SUPPORTED_FIELD_TYPES[f.type]),
               "required": f.required, "label": f.label or f.name[:1].upper() + f.name[1:],
               "display_type": f.type, "sortable": f.sortable, "filterable": f.filterable, "read_only": f.read_only} for f in spec.fields]
    context = {
        "module": spec.module, "pascal": pascal, "camel": camel,
        "entity_name": spec.entity_name, "api_path": spec.api_path,
        "route": spec.route, "title": spec.title, "fields": fields,
        "columns": list(spec.list_columns), "operations": set(spec.operations),
        "search_enabled": spec.list_search_enabled,
        "filter_fields": [f for f in fields if f["filterable"]],
        "editable_fields": [f for f in fields if not f["read_only"] and f["name"] not in {r.field for r in spec.relations}],
        "relations": [{"field": r.field, "name": r.name, "kind": r.kind, "label": r.label,
            "resource": r.resource, "label_field": r.label_field, "value_field": r.value_field,
            "required": r.required, "nullable": r.nullable, "initial_value_field": r.initial_value_field,
            "collection_path": r.collection_path, "item_path": r.item_path,
            "item_response_path": r.item_response_path, "search_param": r.search_param,
            "page_param": r.page_param, "page_size_param": r.page_size_param, "page_size": r.page_size}
            for r in spec.relations],
        "payload_fields": list(dict.fromkeys([f["name"] for f in fields if not f["read_only"]] + [r.field for r in spec.relations])),
        "entity_field_names": [f["name"] for f in fields],
        "response_mode": config["api"]["response_mode"],
        "api_response": {
            "collection_path": spec.api_response.collection_path,
            "item_path": spec.api_response.item_path,
            "total_path": spec.api_response.total_path,
            "page_path": spec.api_response.page_path,
            "page_size_path": spec.api_response.page_size_path,
            "item_response_path": spec.api_response.item_response_path,
            "page_param": spec.api_response.page_param,
            "page_size_param": spec.api_response.page_size_param,
        },
    }
    base = f'{config["paths"]["features_dir"]}/{spec.module}'
    templates = {
        "feature/entity.ts.j2": f"{base}/domain/{camel}.ts",
        "feature/api.ts.j2": f"{base}/infrastructure/{camel}-api.ts",
        "feature/list-model.ts.j2": f"{base}/application/use-{camel}-list-model.ts",
        "feature/columns.ts.j2": f"{base}/presentation/{camel}-columns.ts",
        "feature/renderer-contract.tsx.j2": f"{base}/presentation/{camel}-list-renderer.tsx",
        "feature/route.tsx.j2": f"{base}/presentation/{camel}-route.tsx",
        "feature/form.tsx.j2": f"{base}/presentation/{camel}-form.tsx",
        "feature/README.md.j2": f"{base}/README.md",
        "shared/RelationSelect.tsx.j2": "src/shared/ui/RelationSelect.tsx",
        "shared/RelationSelect.css.j2": "src/shared/ui/RelationSelect.css",
        "shared/item-normalizer.ts.j2": "src/shared/api/item-normalizer.ts",
    }
    return [(str(path), status) for template, relative in templates.items()
            for path, status in [write_file(target, relative, render(template, context), force)]]
