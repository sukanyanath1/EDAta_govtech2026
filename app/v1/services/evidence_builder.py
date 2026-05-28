"""Builds a structured evidence pack from IMF data for a set of countries and indicators."""

from __future__ import annotations

from app.v1.schemas.evidence import EvidencePack, IndicatorRecord
from app.v1.services import imf_client, indicator_catalog_service


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

    for indicator in indicator_codes:
        meta = indicator_catalog_service.get_indicator_metadata(indicator)
        rows = imf_client.get_indicator_for_countries(
            indicator=indicator,
            country_codes=countries,
            years=years,
        )

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
                    source=row.get("source", "IMF DataMapper"),
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
