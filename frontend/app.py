"""Streamlit chat frontend for the EDAta IMF agent."""

from __future__ import annotations

import json

import pandas as pd
import requests
import streamlit as st

from config import settings

# ── Config ─────────────────────────────────────────────────────────────────────

BACKEND_URL = settings.backend_url

st.set_page_config(
    page_title="EDAta Agent",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 EDAta — Economic Intelligence Agent")
st.caption("Ask a diplomatic or economic question. The agent retrieves live IMF data and writes a briefing.")

# ── Session state ──────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages: list[dict] = []

# ── Helpers ────────────────────────────────────────────────────────────────────

def _evidence_to_dataframe(evidence: dict) -> pd.DataFrame | None:
    """Pivot evidence records into a readable country × year table per indicator."""
    records = evidence.get("records", [])
    if not records:
        return None
    rows = []
    for rec in records:
        base = {
            "Country": rec.get("country_name", rec["country_code"]),
            "Indicator": rec.get("indicator_name", rec["indicator_code"]),
            "Unit": rec.get("unit", ""),
        }
        base.update(rec.get("values", {}))
        rows.append(base)
    return pd.DataFrame(rows)


# ── Render history ─────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("evidence"):
            with st.expander("📊 View source data", expanded=False):
                df = _evidence_to_dataframe(msg["evidence"])
                if df is not None:
                    st.dataframe(df, use_container_width=True)

# ── Chat input ─────────────────────────────────────────────────────────────────

if prompt := st.chat_input("e.g. Should we increase engagement with Vietnam?"):
    st.session_state.messages.append({"role": "human", "content": prompt})
    with st.chat_message("human"):
        st.markdown(prompt)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    answer = ""
    evidence_data: dict | None = None

    with st.chat_message("ai"):
        # ── Live progress steps ────────────────────────────────────────────────
        status_container = st.status("Working…", expanded=True)
        answer_placeholder = st.empty()

        try:
            with requests.post(
                f"{BACKEND_URL}/chat/stream",
                json={"message": prompt, "history": history},
                stream=True,
                timeout=180,
            ) as response:
                response.raise_for_status()

                for raw_line in response.iter_lines():
                    if not raw_line:
                        continue
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    if not line.startswith("data: "):
                        continue

                    event = json.loads(line[6:])
                    etype = event.get("type")

                    if etype == "step":
                        status_container.write(f"⚙️ {event['text']}")

                    elif etype == "plan":
                        plan = event["data"]
                        status_container.write(
                            f"📋 Plan: **{plan.get('task_type')}** | "
                            f"bundle: `{plan.get('indicator_bundle')}` | "
                            f"years: {plan.get('start_year')}–{plan.get('end_year')}"
                        )

                    elif etype == "evidence":
                        evidence_data = event["data"]
                        n = len(evidence_data.get("records", []))
                        missing = evidence_data.get("missing", [])
                        status_container.write(
                            f"✅ {n} data records retrieved"
                            + (f" | ⚠️ missing: {', '.join(missing)}" if missing else "")
                        )

                    elif etype == "answer":
                        answer = event["text"]
                        status_container.update(label="Done", state="complete", expanded=False)
                        answer_placeholder.markdown(answer)

                    elif etype == "error":
                        status_container.update(label="Error", state="error", expanded=True)
                        status_container.write(f"❌ {event['text']}")
                        answer = f"⚠️ {event['text']}"
                        answer_placeholder.markdown(answer)

        except requests.exceptions.ConnectionError:
            status_container.update(label="Connection error", state="error")
            answer = (
                f"⚠️ Could not reach the backend at `{BACKEND_URL}`. "
                "Start it with `make run-backend`."
            )
            answer_placeholder.markdown(answer)
        except Exception as exc:  # noqa: BLE001
            status_container.update(label="Error", state="error")
            answer = f"⚠️ Unexpected error: {exc}"
            answer_placeholder.markdown(answer)

        # ── Source data expander ───────────────────────────────────────────────
        if evidence_data:
            with st.expander("📊 View source data (IMF)", expanded=False):
                df = _evidence_to_dataframe(evidence_data)
                if df is not None:
                    st.dataframe(df, use_container_width=True)

    st.session_state.messages.append(
        {"role": "ai", "content": answer, "evidence": evidence_data}
    )

