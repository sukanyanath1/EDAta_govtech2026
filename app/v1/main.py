"""FastAPI application exposing the EDAta IMF agent."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from app.v1.agents import agent_factory
from app.v1.agents.report_agent import build_report_draft
from app.v1.schemas.evidence import EvidencePack
from app.v1.schemas.planning import AnalysisPlan
from app.v1.schemas.report import HtmlReport
from app.v1.services.report_builder import build_chart_specs, build_filename, build_metrics
from app.v1.services.report_renderer import render_html_report

app = FastAPI(
    title="EDAta Agent",
    description="LangChain + OpenAI agent for Azure Data Lake Storage Gen2",
    version="0.2.0",
)


# ── Request / response models ──────────────────────────────────────────────────

class Message(BaseModel):
    role: str   # "human" or "ai"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    response: str


class ReportRequest(BaseModel):
    message: str
    answer: str
    plan: dict
    evidence: dict


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_lc_messages(history: list[Message]) -> list[HumanMessage | AIMessage]:
    mapping = {"human": HumanMessage, "ai": AIMessage}
    result = []
    for msg in history:
        cls = mapping.get(msg.role.lower())
        if cls is None:
            continue
        result.append(cls(content=msg.content))
    return result


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Blocking chat endpoint — returns only the final answer."""
    try:
        answer = agent_factory.run(
            user_input=request.message,
            chat_history=_to_lc_messages(request.history),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(response=answer)


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Streaming SSE endpoint — emits pipeline progress events in real time.

    Each event is a JSON line prefixed with 'data: ', followed by two newlines.

    Event types:
    - step     {"type": "step",     "text": "..."}
    - plan     {"type": "plan",     "data": {...}}
    - evidence {"type": "evidence", "data": {...}}
    - answer   {"type": "answer",   "text": "..."}
    - error    {"type": "error",    "text": "..."}
    - done     {"type": "done"}
    """
    history = _to_lc_messages(request.history)

    def _event_stream():
        for event in agent_factory.run_stream(request.message, history):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@app.post("/report/html", response_model=HtmlReport)
def generate_html_report(request: ReportRequest) -> HtmlReport:
    """Generate an HTML report from an existing analysis answer and evidence pack."""
    try:
        plan = AnalysisPlan.model_validate(request.plan)
        evidence = EvidencePack.model_validate(request.evidence)
        draft = build_report_draft(request.message, request.answer, plan, evidence)
        if not draft.metrics:
            draft.metrics = build_metrics(evidence)
        charts = build_chart_specs(evidence)
        filename = build_filename(plan)
        html = render_html_report(
            draft=draft,
            charts=charts,
            plan=plan,
            user_question=request.message,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return HtmlReport(filename=Path(filename).name, html=html)
