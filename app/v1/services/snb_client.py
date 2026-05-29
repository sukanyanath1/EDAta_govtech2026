"""HTTP client for the Swiss National Bank (SNB) cube REST API.

SNB bilateral data (services trade and FDI) reflects Switzerland's relationship
with each partner country. The SNB cube API serves data as CSV.

Cube reference:
  bopserva  — Balance of Payments, services (credits / debits / net)
  fdiausbla — Swiss direct investment abroad (stocks)

API endpoint:
  https://data.snb.ch/api/cube/{cube}/data/csv?fromDate={YYYY-MM}&toDate={YYYY-MM}

The response is a semicolon-delimited CSV. Country dimension is filtered in-code.
"""

from __future__ import annotations

import io

import pandas as pd
import requests

_BASE_URL = "https://data.snb.ch/api/cube"
_TIMEOUT = 45


def _fetch_cube_csv(cube: str, from_year: int, to_year: int) -> pd.DataFrame | None:
    """Download an SNB cube as a DataFrame. Returns None on failure."""
    url = (
        f"{_BASE_URL}/{cube}/data/csv"
        f"?fromDate={from_year}-01&toDate={to_year}-12"
    )
    try:
        response = requests.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text), sep=";", header=0)
    except Exception:  # noqa: BLE001
        return None


def get_services_trade(
    country_codes: list[str],
    dimension: str,  # "credits" | "debits" | "total" | "country_share"
    years: list[int],
) -> list[dict]:
    """Retrieve Swiss bilateral services trade (BOP) from the SNB.

    Args:
        country_codes: ISO Alpha-3 codes of partner countries.
        dimension:     Which flow to retrieve — credits, debits, total, or country_share.
        years:         List of years to include.

    Returns:
        List of row dicts (one per country) with year columns.
    """
    df = _fetch_cube_csv("bopserva", min(years), max(years))
    if df is None:
        return [{"country_code": c, "indicator_code": f"bopserva_{dimension}", "error": "SNB API unavailable"} for c in country_codes]

    rows = []
    for country_code in country_codes:
        # SNB uses ISO2 or its own country abbreviations — try to match case-insensitively
        mask = df.apply(lambda col: col.astype(str).str.upper() == country_code.upper(), axis=0).any(axis=1)
        country_df = df[mask]

        row = {
            "country_code": country_code,
            "country_name": country_code,
            "indicator_code": f"bopserva_{dimension}",
            "indicator_name": f"Swiss services trade {dimension} — {country_code}",
            "unit": "Millions CHF",
            "source": "SNB",
        }
        for year in years:
            year_col = str(year)
            row[year_col] = float(country_df[year_col].values[0]) if year_col in country_df.columns and not country_df.empty else None

        rows.append(row)

    return rows


def get_fdi_abroad(
    country_codes: list[str],
    dimension: str,  # "stock" | "country_share"
    years: list[int],
) -> list[dict]:
    """Retrieve Swiss direct investment abroad stocks from the SNB.

    Args:
        country_codes: ISO Alpha-3 codes of partner countries.
        dimension:     "stock" for absolute CHF value, "country_share" for percent.
        years:         List of years to include.

    Returns:
        List of row dicts (one per country) with year columns.
    """
    df = _fetch_cube_csv("fdiausbla", min(years), max(years))
    if df is None:
        return [{"country_code": c, "indicator_code": f"fdiausbla_{dimension}", "error": "SNB API unavailable"} for c in country_codes]

    rows = []
    for country_code in country_codes:
        mask = df.apply(lambda col: col.astype(str).str.upper() == country_code.upper(), axis=0).any(axis=1)
        country_df = df[mask]

        row = {
            "country_code": country_code,
            "country_name": country_code,
            "indicator_code": f"fdiausbla_{dimension}",
            "indicator_name": f"Swiss FDI abroad {dimension} — {country_code}",
            "unit": "Millions CHF" if dimension == "stock" else "Percent",
            "source": "SNB",
        }
        for year in years:
            year_col = str(year)
            row[year_col] = float(country_df[year_col].values[0]) if year_col in country_df.columns and not country_df.empty else None

        rows.append(row)

    return rows
