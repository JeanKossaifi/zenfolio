"""Conversion helpers for template-facing data."""

from typing import Any

from zencfg import ConfigBase


def as_dict(value: Any) -> Any:
    """Recursively convert ZenCFG objects into ordinary Python containers."""

    if isinstance(value, ConfigBase):
        return {
            key: as_dict(item)
            for key, item in vars(value).items()
            if not key.startswith("_") and not callable(item)
        }
    if isinstance(value, dict):
        return {key: as_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_dict(item) for item in value]
    return value
