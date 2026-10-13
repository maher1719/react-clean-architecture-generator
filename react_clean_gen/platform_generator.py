from pathlib import Path
from .writer import render, write_file

FILES = {
    "platform/package.json.j2": "package.json",
    "platform/index.html.j2": "index.html",
    "platform/vite.config.ts.j2": "vite.config.ts",
    "platform/tsconfig.json.j2": "tsconfig.json",
    "platform/tsconfig.app.json.j2": "tsconfig.app.json",
    "platform/main.tsx.j2": "src/main.tsx",
    "platform/App.tsx.j2": "src/app/App.tsx",
    "platform/router.tsx.j2": "src/app/router.tsx",
    "platform/navigation.ts.j2": "src/app/navigation.ts",
    "platform/AppLayout.tsx.j2": "src/app/layouts/AppLayout.tsx",
    "platform/NotFoundPage.tsx.j2": "src/app/layouts/NotFoundPage.tsx",
    "platform/tokens.css.j2": "src/styles/tokens.css",
    "platform/global.css.j2": "src/styles/global.css",
    "platform/Button.tsx.j2": "src/shared/ui/Button.tsx",
    "platform/feedback.tsx.j2": "src/shared/feedback/feedback.tsx",
}
def generate_platform(target: Path, context: dict, force=False):
    return [(str(path), status) for template, path in FILES.items()
            for path, status in [write_file(target, path, render(template, context), force)]]
