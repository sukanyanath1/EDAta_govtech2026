"""Schemas for HTML report generation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReportMetric(BaseModel):
    label: str
    value: str
    detail: str = ""


class ReportSection(BaseModel):
    heading: str
    body: str


class ReportChartSeries(BaseModel):
    name: str
    values: list[float | None]


class ReportChart(BaseModel):
    title: str
    chart_type: Literal["line", "bar"]
    unit: str = ""
    note: str = ""
    categories: list[str] = Field(default_factory=list)
    series: list[ReportChartSeries] = Field(default_factory=list)


class ReportDraft(BaseModel):
    title: str
    subtitle: str
    executive_summary: str
    summary_points: list[str] = Field(default_factory=list)
    sections: list[ReportSection] = Field(default_factory=list)
    metrics: list[ReportMetric] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class HtmlReport(BaseModel):
    filename: str
    html: str
