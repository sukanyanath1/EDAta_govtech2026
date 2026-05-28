"""Loads and queries the master indicator catalog and bundles from YAML."""

from __future__ import annotations

import pathlib
from functools import lru_cache
from typing import Any

import yaml

_DATA_DIR = pathlib.Path(__file__).resolve().parents[3] / "data" / "yaml"


@lru_cache(maxsize=1)
def _load_catalog() -> list[dict[str, Any]]:
    return yaml.safe_load((_DATA_DIR / "indicator_catalog.yaml").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_bundles() -> dict[str, Any]:
    return yaml.safe_load((_DATA_DIR / "indicator_bundles.yaml").read_text(encoding="utf-8"))


def get_indicators_for_bundle(bundle_name: str) -> list[str]:
    """Return the list of indicator codes for a given bundle name."""
    bundles = _load_bundles()
    bundle = bundles.get(bundle_name)
    if bundle is None:
        msg = f"Unknown bundle '{bundle_name}'. Available: {list(bundles.keys())}"
        raise ValueError(msg)
    return bundle["indicators"]


def get_indicator_metadata(code: str) -> dict[str, Any] | None:
    """Return catalog metadata for a single indicator code (any source), or None if not found."""
    return next(
        (ind for ind in _load_catalog() if ind.get("code") == code),
        None,
    )


def list_bundles() -> list[str]:
    return list(_load_bundles().keys())


def list_indicators() -> list[dict[str, Any]]:
    return _load_catalog()
