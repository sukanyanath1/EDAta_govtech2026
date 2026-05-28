# Gov Tech Hackathon - EDAta

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

## Use Cases

# IMF
Data Source : [IMF Data](https://data.imf.org/en/datasets/IMF.RES:WEO)