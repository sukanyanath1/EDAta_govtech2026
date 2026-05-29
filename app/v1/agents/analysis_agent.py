"""Analysis agent: turns an evidence pack into a diplomatic briefing."""

from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.v1.config import settings
from app.v1.schemas.evidence import EvidencePack

_ANALYSIS_PROMPT = """\
You are EDAta, an economic intelligence assistant for Swiss diplomats.

Switzerland is always the reference country. All bilateral data (services trade,
FDI) reflects Switzerland's relationship with the partner country.

You have been given a structured evidence pack with data from up to five sources:
  - IMF DataMapper: partner country macroeconomic indicators
  - World Bank: income level / GNI per capita
  - SNB (Swiss National Bank): Switzerland's bilateral services trade and FDI
    - WTO Timeseries API: Switzerland's services trade indicators (Million US dollar)

Write a concise diplomatic briefing based ONLY on the data in the evidence pack.

Rules:
- Do NOT invent numbers. Use only values from the evidence pack.
- Clearly distinguish historical values (before 2026) from forecasts (2026 and beyond).
- Frame findings from Switzerland's perspective: how does this country matter to Switzerland?
- Structure the briefing as:
    1. **Summary Assessment** — 2-3 sentences: strategic relevance to Switzerland
    2. **Evidence Table** — key indicators with most recent values
    3. **Interpretation** — what the data implies for Swiss engagement
    4. **Caveats** — any data gaps, SNB/WTO data not yet loaded, or reliability notes
- If bilateral (SNB/WTO) data is missing or has null values, note the data gap clearly
    and rely on the available indicators for context.
- For trade-balance arguments, compare services exports and imports before any net conclusion.
- Tone: professional, factual, suitable for a government briefing note.

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
    content = result.content
    return content if isinstance(content, str) else str(content)
