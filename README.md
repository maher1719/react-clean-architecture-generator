# react-clean-gen

Independent Python CLI to generate a React + TypeScript + Vite platform and feature modules from YAML.

## Architecture

- `global_config.py`: generator defaults and supported schema types.
- `config.py`: loads the target project's config once per CLI command.
- `platform_generator.py`: creates global app shell files during `init`.
- `api_generator.py`: creates shared HTTP/API infrastructure separately.
- `feature_generator.py`: creates feature-specific types, API methods, list model, columns and renderer contract.
- `templates/`: TypeScript/TSX/CSS templates, separate from Python logic.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Commands

```bash
react-clean-gen init ./frontend
react-clean-gen generate examples/customer.yml --target ./frontend
react-clean-gen show-config --target ./frontend
```

`init` creates the platform, API infrastructure and `react-clean-gen.config.json`.
`generate` loads config once and creates only the selected feature. It does not regenerate global files.
Existing files are skipped by default; use `--force` deliberately.

Generated feature routes are exported for explicit registration rather than automatically editing router source code. This avoids fragile source-code mutation.

## Important

`apiPath` is explicit; the generator does not guess endpoint pluralization. `response_mode` is either `array` or `page-result`. Review the generated contract against the backend API before using it.
