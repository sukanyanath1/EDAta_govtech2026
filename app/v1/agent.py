"""LangChain + OpenAI agent wired up with ADLS Gen2 tools."""

from __future__ import annotations

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.v1.config import settings
from app.v1.tools.adls_tools import ADLS_TOOLS

# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are EDAta, an intelligent data engineering assistant for Azure Data Lake \
Storage Gen2.

You have access to the following tools for interacting with ADLS:
- list_adls_paths   – list files/directories
- read_adls_file    – read a file's text content
- write_adls_file   – create or overwrite a file
- delete_adls_path  – delete a file or directory
- create_adls_directory – create a directory tree

Guidelines:
- Always confirm destructive operations (delete / overwrite) by stating what you are about to do before calling the tool.
- When reading data files, summarise the contents rather than dumping everything unless the user explicitly asks.
- Provide clear, concise answers focused on the user's data engineering task.
"""

# ── LLM & agent factory ────────────────────────────────────────────────────────

def build_agent_executor(
    *,
    verbose: bool = False,
    max_iterations: int = 10,
) -> AgentExecutor:
    """Construct and return a ready-to-use AgentExecutor."""
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
        streaming=True,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm=llm, tools=ADLS_TOOLS, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=ADLS_TOOLS,
        verbose=verbose,
        max_iterations=max_iterations,
        handle_parsing_errors=True,
    )


def run_agent(
    user_input: str,
    chat_history: list[BaseMessage] | None = None,
    *,
    verbose: bool = False,
) -> str:
    """Run the agent with a single user message and return the final answer.

    Args:
        user_input:   The user's natural-language request.
        chat_history: Optional prior conversation turns for multi-turn context.
        verbose:      If True, stream tool call logs to stdout.

    Returns:
        The agent's final text response.
    """
    executor = build_agent_executor(verbose=verbose)
    result = executor.invoke(
        {
            "input": user_input,
            "chat_history": chat_history or [],
        }
    )
    return result["output"]
