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

## Running the Agent

Start the API server:

```bash
make run-agent-demo
```

The server starts at `http://localhost:8000`. Interactive docs are available at `http://localhost:8000/docs`.

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

### Chat with the agent

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

### Use Cases

## Conversational AI
Connect a chatbot to the data lake to 

# IMF data 
Data Source : [IMF Data](https://data.imf.org/en/datasets/IMF.RES:WEO)

# Data

If you add a new dataset, please add it to the topic folder (might not exist yet) and add an entry to the data-catalog.md (see previous as an example)