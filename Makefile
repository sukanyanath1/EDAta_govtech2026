PYTHON := .venv/Scripts/python

.PHONY: run-backend run-frontend run

run-backend:
	$(PYTHON) -m uvicorn app.v1.main:app --reload

run-frontend:
	$(PYTHON) -m streamlit run frontend/app.py

run:
	$(PYTHON) -m uvicorn app.v1.main:app --reload & $(PYTHON) -m streamlit run frontend/app.py

download_imf_data:
	$(PYTHON) scripts/download_imf_data.py
