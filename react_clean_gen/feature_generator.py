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
    fields = [{"name": f.name, "type": SUPPORTED_FIELD_TYPES[f.type],
               "required": f.required, "label": f.label or f.name[:1].upper() + f.name[1:],
               "sortable": f.sortable, "filterable": f.filterable} for f in spec.fields]
    context = {
        "module": spec.module, "pascal": pascal, "camel": camel,
        "entity_name": spec.entity_name, "api_path": spec.api_path,
        "route": spec.route, "title": spec.title, "fields": fields,
        "columns": list(spec.list_columns), "operations": set(spec.operations),
        "response_mode": config["api"]["response_mode"],
    }
    base = f'{config["paths"]["features_dir"]}/{spec.module}'
    templates = {
        "feature/entity.ts.j2": f"{base}/domain/{camel}.ts",
        "feature/api.ts.j2": f"{base}/infrastructure/{camel}-api.ts",
        "feature/list-model.ts.j2": f"{base}/application/use-{camel}-list-model.ts",
        "feature/columns.ts.j2": f"{base}/presentation/{camel}-columns.ts",
        "feature/renderer-contract.tsx.j2": f"{base}/presentation/{camel}-list-renderer.tsx",
        "feature/route.tsx.j2": f"{base}/presentation/{camel}-route.tsx",
        "feature/README.md.j2": f"{base}/README.md",
    }
    return [(str(path), status) for template, relative in templates.items()
            for path, status in [write_file(target, relative, render(template, context), force)]]
