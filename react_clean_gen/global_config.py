"""Generator-wide defaults; separate from target-project configuration."""
DEFAULT_PROJECT_CONFIG = {
    "api": {
        "base_url_env": "VITE_API_BASE_URL",
        "timeout_ms": 15000,
        "response_mode": "page-result",
        "credentials": "same-origin",
    },
    "paths": {"features_dir": "src/features"},
}
SUPPORTED_FIELD_TYPES = {
    "string": "string", "text": "string", "email": "string", "uuid": "string",
    "integer": "number", "number": "number", "boolean": "boolean",
    "date": "string", "datetime": "string",
}
SUPPORTED_OPERATIONS = {"list", "get", "create", "update", "patch", "replace", "delete"}
