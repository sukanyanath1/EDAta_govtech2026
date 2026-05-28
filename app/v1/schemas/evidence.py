"""Pydantic schemas for IMF evidence packs."""

from __future__ import annotations

from pydantic import BaseModel


class IndicatorRecord(BaseModel):
    country_code: str
    country_name: str
    indicator_code: str
    indicator_name: str
    unit: str
    source: str
    values: dict[str, float | None]  # year string → value


class EvidencePack(BaseModel):
    task_type: str
    countries: list[str]
    indicator_codes: list[str]
    start_year: int
    end_year: int
    records: list[IndicatorRecord]
    missing: list[str] = []  # indicator codes with no data
