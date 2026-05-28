# Gov Tech Hackathon - EDAtaBot

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
1. Planner agent       — extracts a structured plan (countries, bundle, year range)
     ↓
2. Indicator resolver  — maps the bundle name to a list of IMF codes
     ↓
3. IMF evidence layer  — fetches data from IMF DataMapper API, builds evidence pack
     ↓
4. Analysis agent      — reads the evidence pack, writes a diplomatic briefing
```

The LLM never calls the IMF API directly and never sees raw HTTP responses. It only reads the structured evidence pack when writing the final answer.

**Project structure:**

```
app/v1/
  agents/
    planner_agent.py      — LLM call #1: question → AnalysisPlan (structured output)
    analysis_agent.py     — LLM call #2: evidence pack → diplomatic briefing
    agent_factory.py      — orchestrates the full pipeline; yields SSE progress events
  services/
    indicator_catalog_service.py  — loads imf_indicator_catalog.yaml and imf_bundles.yaml
    country_resolver.py           — maps country/region names → ISO Alpha-3 codes
    imf_client.py                 — HTTP client for the IMF DataMapper REST API
    evidence_builder.py           — calls imf_client per indicator, returns EvidencePack
  tools/
    imf_tools.py          — 3 semantic LangChain tools
    adls_tools.py         — Azure Data Lake tools (list, read, write, delete files)
  schemas/
    planning.py           — AnalysisPlan Pydantic model
    evidence.py           — EvidencePack + IndicatorRecord Pydantic models
  config.py               — pydantic-settings; reads all env vars from .env
  main.py                 — FastAPI; exposes /chat (blocking) and /chat/stream (SSE)

data/yaml/
  imf_indicator_catalog.yaml  — 11 curated IMF indicators with metadata
  imf_bundles.yaml            — 5 analytical bundles
  country_groups.yaml         — 80+ country aliases + 10 region groups

frontend/
  app.py      — Streamlit chat UI; consumes SSE stream, shows steps + evidence table
  config.py   — frontend settings (BACKEND_URL)
```

**Agents:**

| Agent | File | Role |
|---|---|---|
| Planner | `agents/planner_agent.py` | Extracts `task_type`, countries (ISO codes), bundle, and year range from the user question. No API calls. |
| Analysis | `agents/analysis_agent.py` | Reads the evidence pack and writes a structured diplomatic briefing. No API calls. |
| Factory | `agents/agent_factory.py` | Orchestrates the full pipeline. Emits SSE events: `step`, `plan`, `evidence`, `answer`, `error`, `done`. |

**Indicator bundles:**

| Bundle | Indicators |
|---|---|
| `country_profile` | GDP growth, GDP USD, GDP per capita, inflation, gov. debt, fiscal balance, current account, unemployment, population |
| `macro_risk` | GDP growth, inflation, gov. debt, fiscal balance, current account |
| `trade_potential` | GDP growth, GDP USD, GDP per capita, exports, imports, current account, population |
| `debt_sustainability` | GDP growth, inflation, gov. debt, fiscal balance, current account |
| `investment_assessment` | GDP growth, GDP USD, GDP per capita, inflation, gov. debt, fiscal balance, current account, exports, unemployment |

**LangChain tools:**

| Tool | Description |
|---|---|
| `resolve_country_or_region` | Resolves plain names or regions (e.g. "Vietnam", "ASEAN") to ISO Alpha-3 codes |
| `select_imf_bundle` | Returns indicator codes for a given task type |
| `get_imf_evidence_pack` | Retrieves IMF data for countries and indicators, returns a structured evidence pack |

---

# Use Cases

**Country economic profile**
> "Give me an economic overview of Vietnam."

Uses `country_profile` bundle. Retrieves GDP, inflation, debt, fiscal balance, current account, unemployment, and population.

**Macroeconomic risk assessment**
> "Is Egypt financially vulnerable?" / "Assess macro risks in Argentina."

Uses `macro_risk` bundle. Highlights fiscal pressure, inflation, and external balance signals.

**Trade and investment opportunity**
> "Should we increase economic engagement with Vietnam over the next 5 years?" / "Compare India and Indonesia as trade partners."

Uses `trade_potential` or `investment_assessment` bundle. Includes export/import dynamics, GDP size, and market growth.

**Debt sustainability review**
> "Is Ghana's debt sustainable?" / "Review Sri Lanka's fiscal position."

Uses `debt_sustainability` bundle. Focuses on debt-to-GDP, fiscal deficit, and growth trajectory.

**Multi-country comparison**
> "Compare Vietnam, Thailand, and Indonesia for investment potential."

Includes all countries in the evidence pack and produces a side-by-side briefing.

**Regional assessment**
> "Give me a macro overview of ASEAN." / "Which BRICS country has the strongest growth outlook?"

The country resolver expands region names (e.g. `asean` → 10 ISO codes) automatically.

---

The country resolver expands region names (e.g. `asean` → 10 country codes) automatically.

---

# Data

If you add a new dataset, please add it to the topic folder (might not exist yet) and add an entry to the data-catalog.md (see previous as an example)

