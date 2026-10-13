from pathlib import Path
from jinja2 import Environment, PackageLoader, StrictUndefined

_ENV = Environment(loader=PackageLoader("react_clean_gen", "templates"),
                   undefined=StrictUndefined, autoescape=False,
                   keep_trailing_newline=True, trim_blocks=True, lstrip_blocks=True)

def render(template_name, context):
    return _ENV.get_template(template_name).render(**context)

def write_file(target: Path, relative_path: str, content: str, force=False):
    path = target / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return path, "skipped-existing"
    path.write_text(content, encoding="utf-8")
    return path, "written"
