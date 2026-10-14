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


## Generated feature capabilities

Feature YAML is frontend-specific. The generator supports configurable list columns, server pagination, search via `search`, field filters via `filter[field]`, and create/edit/delete UI when the corresponding operations are declared. The default `update` operation maps to HTTP PATCH; verify this against the backend controller or override the API method template if your backend uses PUT. The backend must implement the query semantics for search and filters; the UI does not pretend to filter all rows client-side.

For relations, the frontend should model the API's public representation, not TypeORM entities. Relation selectors (e.g. author dropdown, tag multi-select) should be generated only after the backend's DTOs, relation lookup endpoints, and write payload contract are explicit.

## Relation selectors (0.4.0)

The React YAML can define form relation controls independently from the NestJS YAML. See `examples/posts.yml` for single-select author/cover-image controls and multi-select tags/co-authors.

```yaml
ui:
  form:
    relations:
      - field: authorId
        name: author
        kind: single
        label: Author
        resource: /api/users
        valueField: id
        labelField: name
        required: true
        response:
          collectionPath: data
          itemPath: props
          itemResponsePath: props
        pagination:
          pageParam: page
          pageSizeParam: limit
          pageSize: 50
      - field: tagIds
        name: tags
        kind: multiple
        label: Tags
        resource: /api/tags
        valueField: id
        labelField: name
        initialValueField: tags
```

- `kind: single` submits one ID (or `null` for a nullable relation); `kind: multiple` submits an array of IDs.
- `resource` must expose a list endpoint with the configured collection/item response paths and a detail endpoint at `resource/:id` for resolving selected labels during edit.
- `searchParam`, `pagination.pageParam`, `pagination.pageSizeParam`, and `pagination.pageSize` configure the lookup request. The backend must implement those query parameters.
- `initialValueField` identifies the field used to prefill an edit form. It may be an ID field such as `authorId` or a relation array such as `tags`; arrays of objects are converted to IDs using `valueField`.
- `api.response.itemResponsePath` configures how detail responses are unwrapped (for example `props`). Set it to an empty string if the endpoint returns the entity directly.
- The generator creates `RelationSelect.tsx`, `RelationSelect.css`, and `item-normalizer.ts` once, and skips existing shared files by default. Use `--force` only when you deliberately want to replace generated files.

The selector is a UI convenience, not authorization or validation. The NestJS backend must verify that referenced IDs exist and that the current user may associate them. A paginated lookup returns only the configured first page; the selector searches remotely and fetches selected IDs individually to hydrate edit forms.

Run `pytest -q` from the generator project to run the generator tests. Install frontend npm dependencies locally and run `npm run build` to verify the generated TypeScript project; the build could not be verified in the current environment because npm dependency installation timed out.
