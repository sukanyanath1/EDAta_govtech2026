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
    """Fetch a single IMF indicator for one or more countries.

    Returns a list of row dicts, one per country, with year columns.
    Missing values are stored as None.
    """
    rows = []

    for country_code in country_codes:
        url = (
            f"{_BASE_URL}/{indicator}/{country_code}"
            f"?periods={','.join(map(str, years))}"
        )

        try:
            response = requests.get(url, timeout=_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            rows.append(
                {
                    "country_code": country_code,
                    "indicator_code": indicator,
                    "error": str(exc),
                }
            )
            continue

        values: dict = (
            data.get("values", {})
            .get(indicator, {})
            .get(country_code, {})
        )

        row = {
            "country_code": country_code,
            "country_name": data.get("countryName", country_code),
            "indicator_code": indicator,
            "indicator_name": data.get("indicatorName", indicator),
            "unit": data.get("units", ""),
            "source": "IMF DataMapper",
        }

        for year in years:
            row[str(year)] = values.get(str(year))

        rows.append(row)

    return rows
