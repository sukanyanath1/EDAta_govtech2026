"""HTTP client for the World Bank REST API v2."""

from __future__ import annotations

import requests

_BASE_URL = "https://api.worldbank.org/v2"
_TIMEOUT = 30


def get_indicator_for_countries(
    indicator: str,
    country_codes: list[str],
    years: list[int],
) -> list[dict]:
    """Fetch a single World Bank indicator for all countries in one request.

    The World Bank API supports semicolon-separated ISO codes:
      /v2/country/VNM;THA;IDN/indicator/{code}?format=json&date=2015:2027
    One HTTP call returns data for all requested countries at once.
    """
    year_range = f"{min(years)}:{max(years)}"
    url = (
        f"{_BASE_URL}/country/{';'.join(country_codes)}/indicator/{indicator}"
        f"?format=json&date={year_range}&per_page=500"
    )

    try:
        response = requests.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        # World Bank returns [metadata_dict, [records]] or [metadata_dict, null]
        if not isinstance(payload, list) or len(payload) < 2:
            return [{"country_code": c, "indicator_code": indicator, "error": "Unexpected response structure"} for c in country_codes]

        records = payload[1] or []
    except requests.RequestException as exc:
        return [{"country_code": c, "indicator_code": indicator, "error": str(exc)} for c in country_codes]

    # Build a lookup: iso3 → {year: value}
    values_by_country: dict[str, dict[str, float | None]] = {}
    name_by_country: dict[str, str] = {}
    indicator_name = indicator

    for rec in records:
        iso3 = rec.get("countryiso3code", "").upper()
        if not iso3:
            continue
        year_str = str(rec.get("date", ""))
        val = rec.get("value")
        values_by_country.setdefault(iso3, {})[year_str] = float(val) if val is not None else None
        name_by_country[iso3] = rec.get("country", {}).get("value", iso3)
        indicator_name = rec.get("indicator", {}).get("value", indicator)

    rows = []
    for country_code in country_codes:
        iso3 = country_code.upper()
        country_vals = values_by_country.get(iso3, {})
        row: dict = {
            "country_code": country_code,
            "country_name": name_by_country.get(iso3, country_code),
            "indicator_code": indicator,
            "indicator_name": indicator_name,
            "unit": "",
            "source": "World Bank",
        }
        for year in years:
            row[str(year)] = country_vals.get(str(year))
        rows.append(row)

    return rows
