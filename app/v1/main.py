"""FastAPI application exposing the EDAta ADLS agent."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from app.v1.agent import run_agent

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
    """Send a message to the ADLS agent and receive a response.

    Pass optional `history` for multi-turn conversations.

    Example body:
    ```json
    {
      "message": "List all files in the raw/ directory",
      "history": []
    }
    ```
    """
    try:
        answer = run_agent(
            user_input=request.message,
            chat_history=_to_lc_messages(request.history),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(response=answer)
