"""Resolves plain country or region names to IMF ISO Alpha-3 codes."""

from __future__ import annotations

import pathlib
from functools import lru_cache

import yaml

_DATA_DIR = pathlib.Path(__file__).resolve().parents[3] / "data" / "yaml"


@lru_cache(maxsize=1)
def _load_groups() -> dict:
    return yaml.safe_load((_DATA_DIR / "country_groups.yaml").read_text(encoding="utf-8"))


def resolve(name: str) -> dict:
    """Resolve a country name, ISO code, or region name.

    Returns:
        {"type": "country", "codes": ["VNM"]}
        or
        {"type": "region", "codes": ["IDN", "MYS", ...]}
    """
    groups = _load_groups()
    key = name.strip().lower()

    # Direct ISO code (3-letter uppercase) — pass through
    if len(key) == 3 and key.upper() == name.upper():
        return {"type": "country", "codes": [key.upper()]}

    # Country alias
    alias_code = groups["aliases"].get(key)
    if alias_code:
        return {"type": "country", "codes": [alias_code]}

    # Region group
    region_codes = groups["regions"].get(key)
    if region_codes:
        return {"type": "region", "codes": region_codes}

    msg = (
        f"Could not resolve '{name}'. "
        "Provide an ISO Alpha-3 code, a known country name, or a region name "
        f"(e.g. asean, brics, g20)."
    )
    raise ValueError(msg)


def resolve_many(names: list[str]) -> list[str]:
    """Resolve a list of names/codes to a flat deduplicated list of ISO codes."""
    codes: list[str] = []
    for name in names:
        result = resolve(name)
        for code in result["codes"]:
            if code not in codes:
                codes.append(code)
    return codes
