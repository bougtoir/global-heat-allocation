"""Configuration loading and validation."""

from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    """Load a YAML configuration file."""
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return config
