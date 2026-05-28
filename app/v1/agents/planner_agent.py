"""Planner agent: extracts a structured AnalysisPlan from a user question."""

from __future__ import annotations

from typing import cast

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.v1.config import settings
from app.v1.schemas.planning import AnalysisPlan
from app.v1.services.indicator_catalog_service import list_bundles

_PLANNER_PROMPT = """\
You are a planning assistant for an economic evidence system used by diplomats.

Your only job is to read the user's question and output a structured JSON plan.
Do NOT retrieve data. Do NOT answer the question. Only produce the plan.

Available task types and bundles:
{bundles}

Rules:
- Resolve country names to ISO Alpha-3 codes (e.g. "Vietnam" → "VNM").
- If the question involves comparing countries, include the primary country in 'countries'
  and comparison countries in 'comparison_countries'.
- Choose the most relevant bundle for the question.
- Default year range: 2015 to 2027 (includes IMF forecasts).
- If the question is clearly about risk or vulnerability, prefer macro_risk or debt_sustainability.
- If the question is about engagement, trade, or opportunity, prefer trade_potential or investment_assessment.
- If it is a general country question, use country_profile.

User question:
{question}

Respond only with valid JSON matching the AnalysisPlan schema. No explanations.
"""


def plan(user_question: str) -> AnalysisPlan:
    """Extract a structured AnalysisPlan from the user's question."""
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    ).with_structured_output(AnalysisPlan)  # SecretStr accepted directly

    prompt = ChatPromptTemplate.from_template(_PLANNER_PROMPT)
    chain = prompt | llm

    return cast(
        AnalysisPlan,
        chain.invoke(
            {
                "bundles": ", ".join(list_bundles()),
                "question": user_question,
            }
        ),
    )
