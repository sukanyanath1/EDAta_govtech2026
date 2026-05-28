"""Client for Swiss Federal Customs Administration (BAZG) SwissImpex trade data.

SwissImpex provides Switzerland's bilateral goods trade statistics.
Portal: https://www.gate.ezv.admin.ch/swissimpex/

Current status: BAZG does not expose a public machine-readable REST API.
Data is available via manual CSV download from the SwissImpex portal.

Implementation strategy:
  - Download annual trade data CSVs from SwissImpex and upload to ADLS.
  - This client reads from ADLS (via Azure Blob) rather than calling BAZG live.
  - Fallback: return None values with a clear source note.

When a CSV is available in ADLS under data/bazg/swissimpex_{year}.csv, set
SWISSIMPEX_ADLS_PATH in .env to enable live reads.
"""

from __future__ import annotations

import os

_ADLS_PATH_ENV = "SWISSIMPEX_ADLS_PATH"
_NOT_AVAILABLE = "BAZG/SwissImpex data not yet loaded. Download CSVs from https://www.gate.ezv.admin.ch/swissimpex/ and upload to ADLS."


def _adls_path() -> str | None:
    return os.getenv(_ADLS_PATH_ENV)


def get_goods_trade(
    country_codes: list[str],
    dimension: str,  # "exports" | "imports" | "total" | "share" | "rank"
    years: list[int],
) -> list[dict]:
    """Retrieve Swiss bilateral goods trade from ADLS-stored SwissImpex CSVs.

    Args:
        country_codes: ISO Alpha-3 codes of partner countries.
        dimension:     exports, imports, total, share, or rank.
        years:         List of years to include.

    Returns:
        List of row dicts (one per country) with year columns, or stub rows
        with None values if data is not yet loaded.
    """
    # If ADLS data is not configured, return informative stubs
    if not _adls_path():
        return [
            {
                "country_code": c,
                "country_name": c,
                "indicator_code": f"swissimpex_{dimension}",
                "indicator_name": f"Swiss goods trade {dimension} — {c}",
                "unit": "Millions CHF" if dimension in ("exports", "imports", "total") else ("Percent" if dimension == "share" else "Rank"),
                "source": "BAZG",
                "note": _NOT_AVAILABLE,
                **{str(y): None for y in years},
            }
            for c in country_codes
        ]

    # TODO: implement ADLS CSV read when data is loaded
    # from app.v1.tools.adls_tools import read_adls_file
    # csv_content = read_adls_file.invoke({"file_path": f"{_adls_path()}/swissimpex_{dimension}.csv"})
    # ... parse and filter by country_code and years
    return [
        {
            "country_code": c,
            "country_name": c,
            "indicator_code": f"swissimpex_{dimension}",
            "indicator_name": f"Swiss goods trade {dimension} — {c}",
            "unit": "Millions CHF",
            "source": "BAZG",
            "note": "ADLS read not yet implemented",
            **{str(y): None for y in years},
        }
        for c in country_codes
    ]
