"""Report agent: turns a briefing and evidence pack into structured report copy."""

from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.v1.config import settings
from app.v1.schemas.evidence import EvidencePack
from app.v1.schemas.planning import AnalysisPlan
from app.v1.schemas.report import ReportDraft

_REPORT_PROMPT = """\
You are preparing a polished HTML briefing for AIDA (AI Diplomatic Assistant),
developed for the Swiss Federal Department of Foreign Affairs (EDA).

Your job is to convert an existing analytical answer plus the structured evidence pack
into clean report copy that fits an official Swiss government briefing format.

Report requirements:
- Audience: Swiss diplomats and policy staff.
- Tone: factual, restrained, executive-ready.
- Do not invent numbers or claims beyond the evidence pack and analysis answer.
- Keep prose concise and readable in an HTML report.
- Prefer Switzerland-facing implications when applicable.
- Produce content that fits these sections:
  1. title
  2. subtitle
  3. executive_summary
  4. 3-5 summary_points
  5. 2-4 body sections with clear headings
  6. 3-6 metrics as short cards
  7. caveats

Template guidance:
- This report will be rendered into an AIDA/EDA branded HTML template.
- Charts are chosen separately by the application, so do not describe chart types.
- Sections should complement the metrics and charts, not repeat raw data line-by-line.

User question:
{question}

Analysis plan:
{plan}

Existing answer:
{answer}

Evidence pack:
{evidence}

Return only valid JSON matching the ReportDraft schema.
"""


def build_report_draft(
    user_question: str,
    answer: str,
    plan: AnalysisPlan,
    evidence: EvidencePack,
) -> ReportDraft:
    """Generate structured report content for HTML rendering."""
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    ).with_structured_output(ReportDraft)

    prompt = ChatPromptTemplate.from_template(_REPORT_PROMPT)
    chain = prompt | llm

    return chain.invoke(
        {
            "question": user_question,
            "plan": json.dumps(plan.model_dump(), indent=2),
            "answer": answer,
            "evidence": json.dumps(evidence.model_dump(), indent=2),
        }
    )
