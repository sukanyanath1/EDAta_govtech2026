"""HTTP client for the WTO Timeseries API (Switzerland-focused trade indicators)."""

from __future__ import annotations

from collections import defaultdict
import time

import pycountry
import requests

from app.v1.config import settings

_BASE_URL = "https://api.wto.org/timeseries/v1/data"
_TIMEOUT = 45
_MIN_SECONDS_BETWEEN_REQUESTS = 1.0
_REPORTER_CODE = "756"  # Switzerland
_TOTAL_PRODUCT_CODE_BY_INDICATOR = {
    "BAT_BV_X": "S",   # Services total in BaTiS
    "BAT_BV_M": "S",   # Services total in BaTiS
    "ITS_MTV_AX": "TO",  # Total merchandise
    "ITS_MTV_AM": "TO",  # Total merchandise
}


def _to_wto_partner_code(country_code: str) -> str:
    """Convert ISO Alpha-3 code to WTO numeric partner code."""
    upper = country_code.upper()
    if upper in {"WLD", "WORLD"}:
        return "000"

    country = pycountry.countries.get(alpha_3=upper)
    if country is None or not getattr(country, "numeric", None):
        msg = f"Unsupported or unknown ISO Alpha-3 code: {country_code}"
        raise ValueError(msg)

    return str(country.numeric).zfill(3)


def _select_rows_for_indicator(dataset: list[dict], indicator: str) -> list[dict]:
    """Prefer total-product rows when available, then fall back to all rows."""
    total_code = _TOTAL_PRODUCT_CODE_BY_INDICATOR.get(indicator)
    if not total_code:
        return dataset

    filtered = [row for row in dataset if str(row.get("ProductOrSectorCode", "")).upper() == total_code]
    return filtered if filtered else dataset


def _build_row(
    *,
    indicator: str,
    partner_code: str,
    partner_name: str,
    years: list[int],
    rows: list[dict],
) -> dict:
    """Build a normalized evidence row with year columns."""
    by_year: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        year = row.get("Year")
        value = row.get("Value")
        if year is None or value is None:
            continue
        try:
            by_year[int(year)].append(float(value))
        except (TypeError, ValueError):
            continue

    first = rows[0] if rows else {}
    result = {
        "country_code": partner_code,
        "country_name": partner_name,
        "indicator_code": indicator,
        "indicator_name": first.get("Indicator", indicator),
        "unit": first.get("Unit", "Million US dollar"),
        "source": "WTO Timeseries API",
    }
    for year in years:
        values = by_year.get(year, [])
        result[str(year)] = sum(values) if values else None

    return result


def get_indicator_for_countries(
    indicator: str,
    country_codes: list[str],
    years: list[int],
) -> list[dict]:
    """Fetch one WTO indicator for Switzerland vs each partner country.

    The WTO endpoint expects query parameters:
      i=<indicator>, r=756 (Switzerland), p=<partner_numeric_code>
    """
    key = settings.wto_subscription_key
    if key is None:
        return [
            {
                "country_code": c,
                "indicator_code": indicator,
                "error": "Missing WTO_SUBSCRIPTION_KEY in environment",
            }
            for c in country_codes
        ]

    subscription_key = key.get_secret_value()
    rows: list[dict] = []
    year_set = set(years)
    last_request_ts: float | None = None

    for country_code in country_codes:
        try:
            partner_code = _to_wto_partner_code(country_code)
        except ValueError as exc:
            rows.append(
                {
                    "country_code": country_code,
                    "indicator_code": indicator,
                    "error": str(exc),
                }
            )
            continue

        params = {
            "i": indicator,
            "r": _REPORTER_CODE,
            "p": partner_code,
            "subscription-key": subscription_key,
        }

        # WTO API limit: max 1 request/second.
        if last_request_ts is not None:
            elapsed = time.monotonic() - last_request_ts
            if elapsed < _MIN_SECONDS_BETWEEN_REQUESTS:
                time.sleep(_MIN_SECONDS_BETWEEN_REQUESTS - elapsed)

        try:
            last_request_ts = time.monotonic()
            response = requests.get(_BASE_URL, params=params, timeout=_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            rows.append(
                {
                    "country_code": country_code,
                    "indicator_code": indicator,
                    "error": str(exc),
                }
            )
            continue

        dataset = payload.get("Dataset") or []
        if not dataset:
            # WTO merchandise indicators can return only world aggregates (p=000)
            # for some reporters/partners, so call this out explicitly.
            if indicator in {"ITS_MTV_AX", "ITS_MTV_AM"} and partner_code != "000":
                error_msg = (
                    "No WTO partner-level goods data returned for this partner "
                    "(indicator currently available as world aggregate only)."
                )
            else:
                error_msg = "No WTO data returned for this partner/indicator"
            rows.append(
                {
                    "country_code": country_code,
                    "indicator_code": indicator,
                    "error": error_msg,
                }
            )
            continue

        selected = _select_rows_for_indicator(dataset, indicator)
        selected = [
            row
            for row in selected
            if row.get("Year") in year_set
        ]

        if not selected:
            rows.append(
                {
                    "country_code": country_code,
                    "indicator_code": indicator,
                    "error": "No WTO data in requested year range",
                }
            )
            continue

        partner_name = str(selected[0].get("PartnerEconomy", country_code))
        rows.append(
            _build_row(
                indicator=indicator,
                partner_code=country_code,
                partner_name=partner_name,
                years=years,
                rows=selected,
            )
        )

    return rows
