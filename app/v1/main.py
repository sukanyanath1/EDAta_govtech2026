"""FastAPI application exposing the EDAta IMF agent."""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from app.v1.agents import agent_factory

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
