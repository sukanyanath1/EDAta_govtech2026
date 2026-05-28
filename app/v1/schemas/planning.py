"""Pydantic schemas for the IMF agent planning and evidence pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisPlan(BaseModel):
    """Structured plan produced by the planner agent before any data retrieval."""

    task_type: str = Field(
        description=(
            "One of: country_profile, macro_risk, trade_potential, "
            "debt_sustainability, investment_assessment"
        )
    )
    countries: list[str] = Field(
        description="List of ISO Alpha-3 country codes to retrieve data for."
    )
    comparison_countries: list[str] = Field(
        default_factory=list,
        description="Optional additional countries for comparison.",
    )
    indicator_bundle: str = Field(
        description="Name of the IMF indicator bundle to use."
    )
    start_year: int = Field(default=2015)
    end_year: int = Field(default=2027)
    include_forecasts: bool = Field(
        default=True,
        description="Whether to include IMF forecast years beyond the current year.",
    )
    output_format: str = Field(
        default="briefing_note",
        description="One of: briefing_note, table_only, summary",
    )
