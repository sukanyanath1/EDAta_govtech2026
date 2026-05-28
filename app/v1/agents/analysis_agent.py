"""Analysis agent: turns an evidence pack into a diplomatic briefing."""

from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.v1.config import settings
from app.v1.schemas.evidence import EvidencePack

_ANALYSIS_PROMPT = """\
You are EDAta, an economic evidence assistant for diplomats.

You have been given a structured evidence pack retrieved from the IMF.
Write a concise diplomatic briefing based ONLY on the data in the evidence pack.

Rules:
- Do NOT invent numbers. Use only values from the evidence pack.
- Clearly distinguish historical values (before 2026) from IMF forecasts (2026 and beyond).
- Structure the answer as: Assessment → Evidence table → Interpretation → Caveats.
- Keep the tone professional and suitable for a government briefing.
- If data is missing for an indicator, note it explicitly.

User question:
{question}

Evidence pack (JSON):
{evidence}

Write the briefing now.
"""


def analyse(user_question: str, evidence: EvidencePack) -> str:
    """Generate a diplomatic briefing from the evidence pack."""
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
        streaming=True,
    )  # SecretStr accepted directly

    prompt = ChatPromptTemplate.from_template(_ANALYSIS_PROMPT)
    chain = prompt | llm

    result = chain.invoke(
        {
            "question": user_question,
            "evidence": json.dumps(evidence.model_dump(), indent=2),
        }
    )
    return result.content
