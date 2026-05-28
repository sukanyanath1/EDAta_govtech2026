# Gov Tech Hackathon - EDAtaBot

EDAta is a **Switzerland-centric diplomatic economic intelligence agent** for Swiss diplomats.
It answers questions about partner countries and bilateral relationships by combining live data from the IMF, World Bank, SNB (Swiss National Bank), and BAZG/SwissImpex into a structured evidence pack, then synthesises a concise diplomatic briefing.

Switzerland is always the reference country. Bilateral data (services trade, FDI, goods trade) always reflects Switzerland's relationship with the partner.

---

# Setup

## Configure the Python environment
<details>
<summary>Click to expand</summary>

- Install `uv`: 

```bash
pip install uv==0.8.14
```

- Create virtual environment: 
```bash
uv venv .venv --python 3.12.11
```

- Activate with: 
```bash
source .venv/Scripts/activate
```

- Install the libraries (including dev): 
```bash
uv pip install -r pyproject.toml

- Install pre-commit: 
```bash
pre-commit install
```

- Adding the environment file
Copy the `env.example` file into `.env` file. Fill in the environment variables.

</details>

## Make Commands

| Command | Description |
|---|---|
| `make run-backend` | Start the FastAPI agent server on `http://localhost:8000` |
| `make run-frontend` | Start the Streamlit chat UI on `http://localhost:8501` |
| `make run` | Start both backend and frontend simultaneously |
| `make download_imf_data` | Download IMF GDP growth data to `data/imf/` |

---

## Running the Agent

**Backend only:**

```bash
make run-backend
```

**Frontend only** (requires backend already running):

```bash
make run-frontend
```

**Both at once:**

```bash
make run
```

This starts uvicorn in the background and Streamlit in the foreground. Press `Ctrl+C` to stop both.

- Backend API + docs: `http://localhost:8000/docs`
- Chat UI: `http://localhost:8501`

---

## API Reference

### Health check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

---

# Chat with the agent

**Single turn:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List all files in the raw/ directory"}'
```

**Multi-turn (pass prior history):**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Now read the first file you found",
    "history": [
      {"role": "human", "content": "List all files in the raw/ directory"},
      {"role": "ai",    "content": "I found the following files: raw/data.csv"}
    ]
  }'
```

**Response shape:**

```json
{"response": "<agent answer>"}
```

---

# IMF data 
Data Source : [IMF Data](https://data.imf.org/en/datasets/IMF.RES:WEO)

# Importing IMF Data

To download IMF GDP growth data and save it to `data/imf/`:

```bash
make download_imf_data
```

> **Note:** Country codes and indicators are currently hardcoded inside `scripts/download_imf_data.py`.
> Edit the `country_code_list` and `indicator_list` variables in `main()` before running.
> CLI parameters will be added tomorrow.

```python
# scripts/download_imf_data.py — edit these lines:
country_code_list = ["DEU"]       # e.g. "USA", "SGP", "FRA"
indicator_list    = ["NGDP_RPCH"] # IMF indicator code
```

IMF country codes follow the ISO Alpha-3 standard. A full list is available at [IMF DataMapper](https://www.imf.org/external/datamapper/api/v1/countries).

---

# Architecture

Every user question flows through a deterministic four-stage pipeline before any LLM synthesis occurs:

```
User question
     ↓
1. Planner agent        — extracts countries (ISO codes), bundle, year range
     ↓
2. Indicator resolver   — maps the bundle to a list of indicator codes
     ↓
3. Evidence layer       — fetches from IMF / World Bank / SNB / BAZG, builds evidence pack
     ↓
4. Analysis agent       — reads evidence pack, writes a Switzerland-perspective briefing
```

The LLM never calls any API directly and never sees raw HTTP responses. It only reads the structured evidence pack when writing the final answer.

**Data sources:**

| Level | Source | Data |
|---|---|---|
| L1 | IMF DataMapper | Partner country macroeconomic indicators (GDP, inflation, debt, etc.) |
| L1 | World Bank | GNI per capita / income category |
| L1 | WIPO | Global Innovation Index rank (static, loaded from ADLS) |
| L2 | SNB — `bopserva` | Switzerland's bilateral services trade (credits, debits, total, share) |
| L3 | SNB — `fdiausbla` | Switzerland's direct investment abroad (stock, country share) |
| L4 | BAZG / SwissImpex | Switzerland's bilateral goods trade (exports, imports, total, share, rank) |

**Project structure:**

```
app/v1/
  agents/
    planner_agent.py      — LLM call #1: question → AnalysisPlan (structured output)
    analysis_agent.py     — LLM call #2: evidence pack → diplomatic briefing
    agent_factory.py      — orchestrates the full pipeline; yields SSE progress events
  services/
    indicator_catalog_service.py  — loads indicator_catalog.yaml and indicator_bundles.yaml
    country_resolver.py           — maps country/region names → ISO Alpha-3 codes
    imf_client.py                 — HTTP client for IMF DataMapper REST API
    worldbank_client.py           — HTTP client for World Bank REST API v2
    snb_client.py                 — HTTP client for SNB cube API (bopserva, fdiausbla)
    swissimpex_client.py          — BAZG goods trade (reads from ADLS; set SWISSIMPEX_ADLS_PATH)
    evidence_builder.py           — routes each indicator to its source client, returns EvidencePack
  tools/
    imf_tools.py          — semantic LangChain tools
    adls_tools.py         — Azure Data Lake tools (list, read, write, delete files)
  schemas/
    planning.py           — AnalysisPlan Pydantic model
    evidence.py           — EvidencePack + IndicatorRecord Pydantic models
  config.py               — pydantic-settings; reads all env vars from .env
  main.py                 — FastAPI; exposes /chat (blocking) and /chat/stream (SSE)

data/yaml/
  indicator_catalog.yaml   — 21 curated indicators across all four sources
  indicator_bundles.yaml   — 6 analytical bundles (Switzerland-centric)
  country_groups.yaml      — 80+ country aliases + 10 region groups

frontend/
  app.py      — Streamlit chat UI; consumes SSE stream, shows steps + evidence table
  config.py   — frontend settings (BACKEND_URL)
```

**Indicator bundles:**

| Bundle | Use when | Data sources |
|---|---|---|
| `ch_bilateral_overview` | Full bilateral picture of any country | IMF + World Bank + SNB + BAZG |
| `ch_trade_partner_assessment` | Trade relevance to Switzerland | IMF + SNB services + BAZG goods |
| `ch_investment_partner_assessment` | FDI attractiveness for Switzerland | IMF + World Bank + SNB FDI |
| `partner_economic_profile` | Partner macro health only | IMF + World Bank |
| `macro_risk` | Financial vulnerability of partner | IMF |
| `debt_sustainability` | Fiscal and debt trajectory | IMF |

**Agents:**

| Agent | File | Role |
|---|---|---|
| Planner | `agents/planner_agent.py` | Extracts `task_type`, countries (ISO codes), bundle, and year range from the user question. No API calls. |
| Analysis | `agents/analysis_agent.py` | Reads evidence pack and writes a Switzerland-perspective diplomatic briefing. No API calls. |
| Factory | `agents/agent_factory.py` | Orchestrates the full pipeline. Emits SSE events: `step`, `plan`, `evidence`, `answer`, `error`, `done`. |

---

# Example Questions

**Full bilateral overview**
> "Give me a full overview of Switzerland's relationship with Vietnam."
> "Prepare a country briefing on India for the State Secretariat."

Uses `ch_bilateral_overview`. Returns IMF macro profile + Swiss services trade (SNB) + Swiss FDI (SNB) + Swiss goods trade (BAZG).

---

**Trade partner assessment**
> "How important is Germany as a trade partner for Switzerland?"
> "Should Switzerland deepen trade ties with Indonesia?"
> "Compare Vietnam, Thailand, and Malaysia as Swiss export markets."

Uses `ch_trade_partner_assessment`. Combines partner economic fundamentals with Swiss bilateral goods and services trade data.

---

**Investment partner assessment**
> "Assess the investment climate in Nigeria from a Swiss perspective."
> "Is Egypt an attractive destination for Swiss FDI?"
> "Compare investment risk in Brazil versus Argentina."

Uses `ch_investment_partner_assessment`. Highlights economic stability, income level, and existing Swiss FDI position.

---

**Partner economic profile**
> "What is Vietnam's economic situation?"
> "Is Turkey financially stable?"

Uses `partner_economic_profile`. IMF + World Bank data on growth, inflation, debt, current account, and income level.

---

**Macro risk**
> "Is Argentina financially vulnerable?"
> "Assess macro risks in Ghana."

Uses `macro_risk`. Focuses on inflation, fiscal balance, debt, and external account signals.

---

**Debt sustainability**
> "Is Sri Lanka's debt sustainable?"
> "Review Kenya's fiscal position."

Uses `debt_sustainability`. GDP growth trajectory against debt-to-GDP, deficit, and current account.

---

**Regional questions**
> "Give me a macro overview of ASEAN."
> "Which BRICS country has the strongest growth outlook for Swiss investment?"
> "How exposed is Switzerland to the Gulf region?"

The country resolver expands region names (e.g. `asean` → 10 ISO codes, `brics`, `g7`, `gulf`, `dach`) automatically.

---

# Data

If you add a new dataset, please add it to the topic folder (might not exist yet) and add an entry to the data-catalog.md (see previous as an example)

