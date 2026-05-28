"""Builds a structured evidence pack from multiple data sources.

Source routing:
  IMF        → imf_client
  World Bank → worldbank_client
  SNB        → snb_client  (bilateral Switzerland ↔ partner)
  BAZG       → swissimpex_client  (bilateral Switzerland ↔ partner goods trade)

All indicators are fetched concurrently (ThreadPoolExecutor) to avoid serial
HTTP round-trips when a bundle has many indicators.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.v1.schemas.evidence import EvidencePack, IndicatorRecord
from app.v1.services import (
    imf_client,
    indicator_catalog_service,
    snb_client,
    swissimpex_client,
    worldbank_client,
)

_MAX_WORKERS = 8


def _fetch_rows(
    indicator: str,
    meta: dict | None,
    countries: list[str],
    years: list[int],
) -> list[dict]:
    """Dispatch data retrieval to the correct source client."""
    source = (meta or {}).get("source", "IMF")

    if source == "IMF":
        return imf_client.get_indicator_for_countries(indicator, countries, years)

    if source == "World Bank":
        return worldbank_client.get_indicator_for_countries(indicator, countries, years)

    if source == "SNB":
        cube = (meta or {}).get("snb_cube", "")
        dimension = (meta or {}).get("snb_dimension", "")
        if cube == "bopserva":
            return snb_client.get_services_trade(countries, dimension, years)
        if cube == "fdiausbla":
            return snb_client.get_fdi_abroad(countries, dimension, years)
        return [{"country_code": c, "indicator_code": indicator, "error": f"Unknown SNB cube: {cube}"} for c in countries]

    if source == "BAZG":
        dimension = indicator.removeprefix("swissimpex_")
        return swissimpex_client.get_goods_trade(countries, dimension, years)

    # Unknown source — fall back to IMF
    return imf_client.get_indicator_for_countries(indicator, countries, years)


def _fetch_one_indicator(
    indicator: str,
    countries: list[str],
    years: list[int],
) -> tuple[str, dict | None, list[dict]]:
    """Fetch a single indicator and return (code, meta, rows) — safe to call concurrently."""
    meta = indicator_catalog_service.get_indicator_metadata(indicator)
    rows = _fetch_rows(indicator, meta, countries, years)
    return indicator, meta, rows


def build_evidence_pack(
    task_type: str,
    countries: list[str],
    indicator_codes: list[str],
    start_year: int,
    end_year: int,
) -> EvidencePack:
    years = list(range(start_year, end_year + 1))
    records: list[IndicatorRecord] = []
    missing: list[str] = []

    # Fetch all indicators concurrently — each source client makes one HTTP call per indicator
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        futures = {
            executor.submit(_fetch_one_indicator, ind, countries, years): ind
            for ind in indicator_codes
        }
        results: dict[str, tuple[dict | None, list[dict]]] = {}
        for future in as_completed(futures):
            indicator, meta, rows = future.result()
            results[indicator] = (meta, rows)

    # Reassemble in original bundle order so the evidence pack is deterministic
    for indicator in indicator_codes:
        meta, rows = results[indicator]

        has_data = False
        for row in rows:
            if "error" in row:
                continue
            year_values = {str(y): row.get(str(y)) for y in years}
            records.append(
                IndicatorRecord(
                    country_code=row["country_code"],
                    country_name=row.get("country_name", row["country_code"]),
                    indicator_code=indicator,
                    indicator_name=row.get("indicator_name", meta["name"] if meta else indicator),
                    unit=row.get("unit", meta["unit"] if meta else ""),
                    source=row.get("source", (meta or {}).get("source", "Unknown")),
                    values=year_values,
                )
            )
            has_data = True

        if not has_data:
            missing.append(indicator)

    return EvidencePack(
        task_type=task_type,
        countries=countries,
        indicator_codes=indicator_codes,
        start_year=start_year,
        end_year=end_year,
        records=records,
        missing=missing,
    )
