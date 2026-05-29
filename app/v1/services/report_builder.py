"""Helpers for preparing report metadata and chart specs."""

from __future__ import annotations

import re
from collections import defaultdict

from app.v1.schemas.evidence import EvidencePack, IndicatorRecord
from app.v1.schemas.planning import AnalysisPlan
from app.v1.schemas.report import ReportChart, ReportChartSeries, ReportMetric


def slugify(value: str) -> str:
    """Create a filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "aida-report"


def build_filename(plan: AnalysisPlan) -> str:
    """Build a deterministic report filename."""
    countries = "-".join(code.lower() for code in plan.countries[:2]) or "briefing"
    return f"aida-report-{countries}-{plan.task_type}.html"


def build_metrics(evidence: EvidencePack, limit: int = 4) -> list[ReportMetric]:
    """Select a few recent indicators for summary cards."""
    metrics: list[ReportMetric] = []
    for record in evidence.records:
        latest = _latest_point(record)
        if latest is None:
            continue
        year, value = latest
        metrics.append(
            ReportMetric(
                label=f"{record.country_name} - {record.indicator_name}",
                value=_format_value(value, record.unit),
                detail=f"Latest available year: {year}",
            )
        )
        if len(metrics) >= limit:
            break
    return metrics


def build_chart_specs(evidence: EvidencePack, limit: int = 2) -> list[ReportChart]:
    """Choose simple, deterministic charts from the evidence pack."""
    charts: list[ReportChart] = []

    trend_candidate = _best_trend_record(evidence.records)
    if trend_candidate is not None:
        categories, values = _sorted_points(trend_candidate)
        charts.append(
            ReportChart(
                title=f"Trend: {trend_candidate.country_name} - {trend_candidate.indicator_name}",
                chart_type="line",
                unit=trend_candidate.unit,
                note="Automatically selected because the evidence includes a consistent multi-year time series.",
                categories=categories,
                series=[
                    ReportChartSeries(
                        name=trend_candidate.country_name,
                        values=values,
                    )
                ],
            )
        )

    comparison_candidate = _best_comparison_chart(evidence.records)
    if comparison_candidate is not None:
        charts.append(comparison_candidate)

    return charts[:limit]


def _best_trend_record(records: list[IndicatorRecord]) -> IndicatorRecord | None:
    candidates = [record for record in records if _numeric_point_count(record) >= 4]
    if not candidates:
        return None
    candidates.sort(
        key=lambda record: (
            _indicator_priority(record.indicator_name),
            _numeric_point_count(record),
        ),
        reverse=True,
    )
    return candidates[0]


def _best_comparison_chart(records: list[IndicatorRecord]) -> ReportChart | None:
    grouped: dict[tuple[str, str], list[IndicatorRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.indicator_code, record.indicator_name)].append(record)

    candidates: list[tuple[int, ReportChart]] = []
    for (_, indicator_name), group in grouped.items():
        if len(group) < 2:
            continue
        latest_points = []
        for record in group:
            latest = _latest_point(record)
            if latest is None:
                continue
            year, value = latest
            latest_points.append((record.country_name, year, value, record.unit))
        if len(latest_points) < 2:
            continue

        latest_points.sort(key=lambda item: item[0])
        categories = [country for country, _, _, _ in latest_points]
        values = [value for _, _, value, _ in latest_points]
        common_year = max(year for _, year, _, _ in latest_points)
        unit = next((unit for _, _, _, unit in latest_points if unit), "")
        chart = ReportChart(
            title=f"Comparison: {indicator_name}",
            chart_type="bar",
            unit=unit,
            note=f"Automatically selected to compare the most recent values across countries (latest year observed: {common_year}).",
            categories=categories,
            series=[ReportChartSeries(name=indicator_name, values=values)],
        )
        candidates.append((len(latest_points), chart))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _indicator_priority(indicator_name: str) -> int:
    name = indicator_name.lower()
    priorities = (
        "gdp",
        "inflation",
        "trade",
        "exports",
        "imports",
        "current account",
        "debt",
        "unemployment",
    )
    for index, keyword in enumerate(priorities[::-1], start=1):
        if keyword in name:
            return len(priorities) - index + 1
    return 0


def _numeric_point_count(record: IndicatorRecord) -> int:
    return sum(1 for value in record.values.values() if value is not None)


def _sorted_points(record: IndicatorRecord) -> tuple[list[str], list[float | None]]:
    pairs = sorted(record.values.items(), key=lambda item: item[0])
    categories = [year for year, value in pairs if value is not None]
    values = [value for _, value in pairs if value is not None]
    return categories, values


def _latest_point(record: IndicatorRecord) -> tuple[str, float] | None:
    pairs = [(year, value) for year, value in record.values.items() if value is not None]
    if not pairs:
        return None
    year, value = max(pairs, key=lambda item: item[0])
    return year, value


def _format_value(value: float, unit: str) -> str:
    if abs(value) >= 100:
        formatted = f"{value:,.1f}"
    else:
        formatted = f"{value:.2f}"
    return f"{formatted} {unit}".strip()
