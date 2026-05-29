"""Render AIDA HTML reports from template data."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from app.v1.schemas.planning import AnalysisPlan
from app.v1.schemas.report import ReportChart, ReportDraft, ReportMetric, ReportSection

_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "aida_report.html"


def render_html_report(
    *,
    draft: ReportDraft,
    charts: list[ReportChart],
    plan: AnalysisPlan,
    user_question: str,
) -> str:
    """Render the HTML report template."""
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "__TITLE__": escape(draft.title),
        "__SUBTITLE__": escape(draft.subtitle),
        "__QUESTION__": escape(user_question),
        "__TASK_TYPE__": escape(plan.task_type.replace("_", " ").title()),
        "__COUNTRIES__": escape(", ".join(plan.countries + plan.comparison_countries) or "Switzerland"),
        "__EXECUTIVE_SUMMARY__": _paragraphs(draft.executive_summary),
        "__SUMMARY_POINTS__": _bullet_list(draft.summary_points),
        "__METRICS__": _metrics_html(draft.metrics),
        "__SECTIONS__": _sections_html(draft.sections),
        "__CAVEATS__": _bullet_list(draft.caveats),
        "__CHART_SPECS__": json.dumps([chart.model_dump() for chart in charts]),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def _paragraphs(text: str) -> str:
    paragraphs = [segment.strip() for segment in text.split("\n") if segment.strip()]
    return "".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs)


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "<li>No additional points provided.</li>"
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def _metrics_html(metrics: list[ReportMetric]) -> str:
    if not metrics:
        return '<article class="metric-card"><h3>No metrics available</h3><p>Evidence did not contain display-ready values.</p></article>'
    return "".join(
        (
            '<article class="metric-card">'
            f"<h3>{escape(metric.label)}</h3>"
            f"<strong>{escape(metric.value)}</strong>"
            f"<p>{escape(metric.detail)}</p>"
            "</article>"
        )
        for metric in metrics
    )


def _sections_html(sections: list[ReportSection]) -> str:
    if not sections:
        return ""
    return "".join(
        (
            '<section class="report-section">'
            f"<h2>{escape(section.heading)}</h2>"
            f"{_paragraphs(section.body)}"
            "</section>"
        )
        for section in sections
    )
