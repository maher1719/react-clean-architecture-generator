from pathlib import Path
from .writer import render, write_file

FILES = {
    "api/http-client.ts.j2": "src/shared/api/http-client.ts",
    "api/api-error.ts.j2": "src/shared/api/api-error.ts",
    "api/api-config.ts.j2": "src/shared/api/api-config.ts",
    "api/api-types.ts.j2": "src/shared/api/api-types.ts",
}
def generate_api_infrastructure(target: Path, config: dict, force=False):
    context = {
        "api_base_env": config["base_url_env"],
        "timeout_ms": config["timeout_ms"],
        "credentials": config["credentials"],
    }
    return [(str(path), status) for template, path in FILES.items()
            for path, status in [write_file(target, path, render(template, context), force)]]
