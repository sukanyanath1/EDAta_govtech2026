"""Agent factory: wires the full planner → retrieval → analysis pipeline."""

from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

from langchain_core.messages import BaseMessage

from app.v1.agents import analysis_agent, planner_agent
from app.v1.schemas.evidence import EvidencePack
from app.v1.schemas.planning import AnalysisPlan
from app.v1.services import evidence_builder, indicator_catalog_service


def _event(type_: str, **kwargs: Any) -> dict:
    return {"type": type_, **kwargs}


def run_stream(
    user_input: str,
    chat_history: list[BaseMessage] | None = None,
) -> Generator[dict, None, None]:
    """Run the full IMF pipeline, yielding progress events at each stage.

    Event types:
    - step     {"text": str}               — progress message for the UI
    - plan     {"data": dict}              — the AnalysisPlan extracted by the planner
    - evidence {"data": dict}              — the full evidence pack (source data)
    - answer   {"text": str}               — the final diplomatic briefing
    - error    {"text": str}               — pipeline error
    - done     {}                          — signals end of stream
    """
    # ── Step 1: Plan ──────────────────────────────────────────────────────────
    yield _event("step", text="Planning your question…")
    try:
        plan: AnalysisPlan = planner_agent.plan(user_input)
    except Exception as exc:  # noqa: BLE001
        yield _event("error", text=f"Planner failed: {exc}")
        yield _event("done")
        return

    yield _event("plan", data=plan.model_dump())
    yield _event(
        "step",
        text=f"Countries identified: {', '.join(plan.countries + plan.comparison_countries)}",
    )

    # ── Step 2: Resolve bundle ────────────────────────────────────────────────
    try:
        indicator_codes = indicator_catalog_service.get_indicators_for_bundle(
            plan.indicator_bundle
        )
    except Exception as exc:  # noqa: BLE001
        yield _event("error", text=f"Bundle resolution failed: {exc}")
        yield _event("done")
        return

    yield _event(
        "step",
        text=f"Bundle selected: {plan.indicator_bundle} — {len(indicator_codes)} indicators",
    )
    for code in indicator_codes:
        meta = indicator_catalog_service.get_indicator_metadata(code)
        label = meta["name"] if meta else code
        yield _event("step", text=f"Fetching {label} ({code})…")

    # ── Step 3: Retrieve evidence ─────────────────────────────────────────────
    all_countries = plan.countries + plan.comparison_countries
    try:
        evidence: EvidencePack = evidence_builder.build_evidence_pack(
            task_type=plan.task_type,
            countries=all_countries,
            indicator_codes=indicator_codes,
            start_year=plan.start_year,
            end_year=plan.end_year,
        )
    except Exception as exc:  # noqa: BLE001
        yield _event("error", text=f"Data retrieval failed: {exc}")
        yield _event("done")
        return

    yield _event(
        "step",
        text=f"Evidence pack ready — {len(evidence.records)} records retrieved"
        + (f", {len(evidence.missing)} indicators missing" if evidence.missing else ""),
    )
    yield _event("evidence", data=evidence.model_dump())

    # ── Step 4: Analyse ───────────────────────────────────────────────────────
    yield _event("step", text="Writing diplomatic briefing…")
    try:
        answer = analysis_agent.analyse(user_input, evidence)
    except Exception as exc:  # noqa: BLE001
        yield _event("error", text=f"Analysis failed: {exc}")
        yield _event("done")
        return

    yield _event("answer", text=answer)
    yield _event("done")


def run(
    user_input: str,
    chat_history: list[BaseMessage] | None = None,
) -> str:
    """Blocking version — drains the stream and returns only the final answer."""
    answer = ""
    for event in run_stream(user_input, chat_history):
        if event["type"] == "answer":
            answer = event["text"]
        elif event["type"] == "error":
            raise RuntimeError(event["text"])
    return answer
