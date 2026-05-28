"""Streamlit chat frontend for the EDAta agent."""

import requests
import streamlit as st

from frontend.config import settings

# ── Config ─────────────────────────────────────────────────────────────────────

BACKEND_URL = settings.backend_url

st.set_page_config(
    page_title="EDAta Agent",
    page_icon="🗂️",
    layout="centered",
)

st.title("🗂️ EDAta Agent")
st.caption("Ask questions about your Azure Data Lake — list files, read data, and more.")

# ── Session state ──────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages: list[dict] = []

# ── Render history ─────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ─────────────────────────────────────────────────────────────────

if prompt := st.chat_input("e.g. List all files in raw/"):
    # Show user message immediately
    st.session_state.messages.append({"role": "human", "content": prompt})
    with st.chat_message("human"):
        st.markdown(prompt)

    # Build history payload (exclude the message we just added)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    # Call backend
    with st.chat_message("ai"):
        with st.spinner("Thinking…"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={"message": prompt, "history": history},
                    timeout=120,
                )
                response.raise_for_status()
                answer = response.json()["response"]
            except requests.exceptions.ConnectionError:
                answer = (
                    "⚠️ Could not reach the backend. "
                    f"Is the agent running at `{BACKEND_URL}`? "
                    "Start it with `make run-agent-demo`."
                )
            except requests.exceptions.HTTPError as e:
                answer = f"⚠️ Backend error: {e.response.status_code} — {e.response.text}"
            except Exception as e:  # noqa: BLE001
                answer = f"⚠️ Unexpected error: {e}"

        st.markdown(answer)

    st.session_state.messages.append({"role": "ai", "content": answer})
