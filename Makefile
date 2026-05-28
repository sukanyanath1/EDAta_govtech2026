PYTHON := .venv/Scripts/python

.PHONY: run-agent-demo

run-agent-demo:
	$(PYTHON) -m uvicorn app.v1.main:app --reload

download_imf_data:
	$(PYTHON) scripts/download_imf_data.py
