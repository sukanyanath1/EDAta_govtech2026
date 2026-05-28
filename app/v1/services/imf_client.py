"""HTTP client for the IMF DataMapper API."""

from __future__ import annotations

import requests

_BASE_URL = "https://www.imf.org/external/datamapper/api/v1"
_TIMEOUT = 30


def get_indicator_for_countries(
    indicator: str,
    country_codes: list[str],
    years: list[int],
) -> list[dict]:
    """Fetch a single IMF indicator for all countries in one request.

    The IMF DataMapper API supports multiple countries in the URL path:
      /api/v1/{indicator}/{iso1}/{iso2}/...?periods=2015,2016,...
    One HTTP call returns data for all requested countries at once.
    """
    url = (
        f"{_BASE_URL}/{indicator}/{'/'.join(country_codes)}"
        f"?periods={','.join(map(str, years))}"
    )

    try:
        response = requests.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return [
            {"country_code": c, "indicator_code": indicator, "error": str(exc)}
            for c in country_codes
        ]

    # Response shape: values[indicator][country][year], entities[country]{label}, indicators[code]{label,unit}
    indicator_values: dict = data.get("values", {}).get(indicator, {})
    entities: dict = data.get("entities", {})
    indicator_meta: dict = data.get("indicators", {}).get(indicator, {})
    indicator_label: str = indicator_meta.get("label", indicator)
    unit: str = indicator_meta.get("unit", "")

    rows = []
    for country_code in country_codes:
        country_values: dict = indicator_values.get(country_code, {})
        country_label: str = entities.get(country_code, {}).get("label", country_code)

        row: dict = {
            "country_code": country_code,
            "country_name": country_label,
            "indicator_code": indicator,
            "indicator_name": indicator_label,
            "unit": unit,
            "source": "IMF DataMapper",
        }
        for year in years:
            row[str(year)] = country_values.get(str(year))

        rows.append(row)

    return rows
