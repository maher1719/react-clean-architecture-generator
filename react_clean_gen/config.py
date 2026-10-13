"""Project config loading/writing. Loaded once per CLI invocation."""
import json
from pathlib import Path
from .global_config import DEFAULT_PROJECT_CONFIG

CONFIG_FILENAME = "react-clean-gen.config.json"

def merge(base, override):
    result = dict(base)
    for key, value in override.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
    return result

def write_default_project_config(target: Path, force=False):
    target.mkdir(parents=True, exist_ok=True)
    path = target / CONFIG_FILENAME
    if not path.exists() or force:
        path.write_text(json.dumps(DEFAULT_PROJECT_CONFIG, indent=2) + "\n", encoding="utf-8")
    return path

def load_project_config(target: Path):
    path = target / CONFIG_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Missing {CONFIG_FILENAME}; run `react-clean-gen init {target}` first.")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{CONFIG_FILENAME} must contain a JSON object.")
    config = merge(DEFAULT_PROJECT_CONFIG, raw)
    if config["api"]["response_mode"] not in {"array", "page-result"}:
        raise ValueError("api.response_mode must be 'array' or 'page-result'.")
    if not isinstance(config["api"]["timeout_ms"], int) or config["api"]["timeout_ms"] <= 0:
        raise ValueError("api.timeout_ms must be a positive integer.")
    return config
