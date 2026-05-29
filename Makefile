PYTHON := .venv/Scripts/python

.PHONY: run-backend run-frontend run docker-build docker-run docker-down deploy-azure

run-backend:
	$(PYTHON) -m uvicorn app.v1.main:app --reload

run-frontend:
	$(PYTHON) -m streamlit run frontend/app.py

run:
	$(PYTHON) -m uvicorn app.v1.main:app --reload & $(PYTHON) -m streamlit run frontend/app.py

download_imf_data:
	$(PYTHON) scripts/download_imf_data.py

# ── Docker (local) ────────────────────────────────────────────────────────────
docker-build:
	docker compose build

docker-run:
	docker compose up --build

docker-down:
	docker compose down

# ── Azure Container Apps ──────────────────────────────────────────────────────
deploy-azure:
	bash scripts/azure-deploy.sh
