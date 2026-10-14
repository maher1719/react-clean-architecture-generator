# react-clean-gen

Independent Python CLI to generate a React + TypeScript + Vite platform and feature modules from YAML.

## Architecture

- `global_config.py`: generator-wide defaults and supported schema types.
- `config.py`: loads the target project's config once per CLI command.
- `platform_generator.py`: creates the global app shell once during `init`.
- `api_generator.py`: creates the shared HTTP client, API types, and response normalization helper.
- `feature_generator.py`: creates a feature's entity types, API methods, list model, column metadata, actual table renderer, and route export.
- `templates/`: TypeScript/TSX/CSS templates, separate from Python generation logic.

Backend and frontend configurations are independent. The NestJS generator owns its own YAML. This React generator accepts a React-focused YAML and validates its API response mapping; it does not mutate or depend on the NestJS generator's files.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Generate a platform and Users feature

```bash
react-clean-gen init ./frontend
react-clean-gen generate examples/user.yml --target ./frontend
```

The `init` command generates the global platform and shared API infrastructure. The `generate` command generates only the requested feature; it does not rewrite global files.

Generated feature routes are exported for explicit registration. Add `userRoute` to the children of the root route in `src/app/router.tsx`, and add `userNavigationItem` to `src/app/navigation.ts` if you want the feature in the navigation. This is intentionally explicit instead of fragile source-code mutation.

Set `VITE_API_BASE_URL` in a local `.env` if the backend is hosted on a different origin. The example endpoint is `/api/users`; update `api.path` to match your actual NestJS route.

## API response mapping

`examples/user.yml` is configured for this paginated response shape:

```json
{
  "data": [{ "props": { "id": "...", "name": "maher", "email": "ben abdessalem", "createdAt": "2026-10-04T05:29:40.067Z", "updatedAt": "2026-10-04T05:29:40.067Z" } }],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

The generated API adapter unwraps `data[].props` and normalizes the response to `PageResult<T>` (`items`, `totalItems`, `page`, `pageSize`, `totalPages`). The table and list model do not know about the backend-specific `props` wrapper. Response paths and query parameter names are configurable in the React YAML.

## First vertical slice

- Configurable native HTML table and column labels.
- Date/datetime and boolean display formatting.
- Loading, error, retry, and empty states.
- Server-side pagination using `page` and `limit` query parameters.
- Configurable page sizes (10, 20, 50, 100).
- Fetch cancellation on query changes/unmount to avoid stale responses.

Search, filtering, sorting, create/edit forms, and delete flows are intentionally not represented as implemented UI yet. The schema has placeholders for future query options, but backend support must be verified before those controls are enabled.

## Safety and generation behavior

Existing files are skipped by default. Use `--force` deliberately; it overwrites generated targets. Back up customizations before forcing regeneration.

```bash
react-clean-gen show-config --target ./frontend
```

## Relation fields

Version 0.4.0 supports `ui.form.relations` in feature YAML. Each relation specifies `field` (write-payload key), `kind` (`single` or `multiple`), `resource`, `valueField`, and `labelField`. Optional response paths configure list/detail wrapper formats. Use `initialValueField` to hydrate edits from ID fields or nested relation values. See `examples/posts.yml` for a full example.

The generator emits reusable shared relation-select components and an item-response normalizer. Lookup endpoints must support the configured search and pagination query parameters and `GET /resource/:id` for selected-label hydration. Backend validation and authorization remain mandatory.
