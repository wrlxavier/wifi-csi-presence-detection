"""Configuration loader for YAML configuration files."""

from pathlib import Path
from typing import Any
import yaml


class ConfigDict(dict):
    """Dictionary subclass supporting attribute-style dot access."""

    def __getattr__(self, key: str) -> Any:
        try:
            val = self[key]
            if isinstance(val, dict) and not isinstance(val, ConfigDict):
                val = ConfigDict(val)
                self[key] = val
            return val
        except KeyError:
            raise AttributeError(f"Config has no attribute {key!r}")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def load_yaml_config(config_path: str | Path) -> ConfigDict:
    """Load a YAML configuration file as a ConfigDict."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return ConfigDict(data)
