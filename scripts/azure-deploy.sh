#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# EDAta — Azure Container Apps deployment
# Region: switzerlandnorth  (closest to target users)
#
# Prerequisites:
#   az login
#   az extension add --name containerapp --upgrade
#
# Usage:
#   ./scripts/azure-deploy.sh
#
# Requires Docker Desktop (builds images locally and pushes to ACR).
# Secrets are read automatically from .env in the project root.
# Any var already set in the shell takes precedence over .env.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Load .env (shell vars take precedence if already set) ─────────────────────
ENV_FILE="$(dirname "$0")/../.env"
if [ -f "$ENV_FILE" ]; then
  set -a                  # mark all new vars for export
  # shellcheck source=../.env
  source "$ENV_FILE"
  set +a
  echo "✓ Loaded secrets from .env"
else
  echo "⚠ No .env file found — falling back to shell environment"
fi

# ── Configuration ─────────────────────────────────────────────────────────────
RESOURCE_GROUP="${RESOURCE_GROUP:-edatademo-rg}"
LOCATION="${LOCATION:-switzerlandnorth}"
ACR_NAME="${ACR_NAME:-edatademoregistry}"      # must be globally unique, lowercase
ENVIRONMENT="${ENVIRONMENT:-edatademo-env}"
BACKEND_APP="${BACKEND_APP:-edatademo-backend}"
FRONTEND_APP="${FRONTEND_APP:-edatademo-frontend}"

# Required env vars (set before running this script)
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running}"
: "${OPENAI_MODEL:?Set OPENAI_MODEL before running}"
: "${STORAGE_ACCOUNT_URL:?Set STORAGE_ACCOUNT_URL before running}"
: "${ADLS_FILESYSTEM:?Set ADLS_FILESYSTEM before running}"
ADLS_SAS_TOKEN="${ADLS_SAS_TOKEN:-}"

# ── Image naming (read from pyproject.toml) ───────────────────────────────────
PYPROJECT="$(dirname "$0")/../pyproject.toml"
APP_NAME=$(grep '^name' "$PYPROJECT" | head -1 | sed 's/.*= *"\(.*\)"/\1/' | tr '[:upper:]' '[:lower:]')
APP_VERSION=$(grep '^version' "$PYPROJECT" | head -1 | sed 's/.*= *"\(.*\)"/\1/')
VER_MAJOR="${APP_VERSION%%.*}"
VER_MINOR="${APP_VERSION%.*}"   # strips patch  → e.g. 0.1
BACKEND_IMAGE="$APP_NAME/backend:$APP_VERSION"
FRONTEND_IMAGE="$APP_NAME/frontend:$APP_VERSION"

echo "==> Deploying EDAta to Azure Container Apps"
echo "    Resource group : $RESOURCE_GROUP"
echo "    Region         : $LOCATION"
echo "    ACR            : $ACR_NAME"
echo "    Image tag      : $APP_NAME:$APP_VERSION"

# ── 1. Resource group ─────────────────────────────────────────────────────────
# Ensure required resource providers are registered (no-op if already registered)
az provider register --namespace Microsoft.ContainerRegistry --wait --output none
az provider register --namespace Microsoft.App --wait --output none
az provider register --namespace Microsoft.OperationalInsights --wait --output none
echo "✓ Resource providers registered"

az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none
echo "✓ Resource group ready"

# ── 2. Azure Container Registry ───────────────────────────────────────────────
if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --output none 2>/dev/null; then
  echo "  ACR already exists in this resource group, skipping creation"
else
  az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none
fi

ACR_SERVER="${ACR_NAME}.azurecr.io"
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query "passwords[0].value" -o tsv)
echo "✓ ACR ready: $ACR_SERVER"

# ── 3. Build & push images ────────────────────────────────────────────────────
echo "==> Building images locally and pushing to ACR..."
az acr login --name "$ACR_NAME"

docker build -f Dockerfile.backend \
  -t "$ACR_SERVER/$APP_NAME/backend:$APP_VERSION" \
  -t "$ACR_SERVER/$APP_NAME/backend:$VER_MINOR" \
  -t "$ACR_SERVER/$APP_NAME/backend:$VER_MAJOR" \
  .
docker push "$ACR_SERVER/$APP_NAME/backend:$APP_VERSION"
docker push "$ACR_SERVER/$APP_NAME/backend:$VER_MINOR"
docker push "$ACR_SERVER/$APP_NAME/backend:$VER_MAJOR"

docker build -f Dockerfile.frontend \
  -t "$ACR_SERVER/$APP_NAME/frontend:$APP_VERSION" \
  -t "$ACR_SERVER/$APP_NAME/frontend:$VER_MINOR" \
  -t "$ACR_SERVER/$APP_NAME/frontend:$VER_MAJOR" \
  .
docker push "$ACR_SERVER/$APP_NAME/frontend:$APP_VERSION"
docker push "$ACR_SERVER/$APP_NAME/frontend:$VER_MINOR"
docker push "$ACR_SERVER/$APP_NAME/frontend:$VER_MAJOR"

echo "✓ Images pushed to $ACR_SERVER"

# ── Helper: create on first deploy, update image on redeploy ──────────────────
# Container App ingress/ports/scale are set at create time and don't change.
# On redeploy we only need to update the image (and optionally secrets/env-vars).
_upsert_containerapp() {
  local name="$1"; shift   # remaining args are for `create` only
  if az containerapp show --name "$name" --resource-group "$RESOURCE_GROUP" \
       --output none 2>/dev/null; then
    echo "  '$name' already exists — updating image..."
    az containerapp update \
      --name "$name" \
      --resource-group "$RESOURCE_GROUP" \
      --image "$ACR_SERVER/$APP_NAME/${name##*-}:$APP_VERSION" \
      --output none
  else
    echo "  Creating '$name'..."
    az containerapp create --name "$name" --resource-group "$RESOURCE_GROUP" "$@" --output none
  fi
}

# ── 4. Container Apps environment ─────────────────────────────────────────────
if az containerapp env show --name "$ENVIRONMENT" --resource-group "$RESOURCE_GROUP" --output none 2>/dev/null; then
  echo "  Container Apps environment already exists, skipping creation"
else
  az containerapp env create \
    --name "$ENVIRONMENT" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --logs-destination none \
    --output none
fi
echo "✓ Container Apps environment ready"

# ── 5. Deploy backend (internal ingress — not exposed to the public internet) ─
echo "==> Deploying backend..."

BACKEND_SECRETS=("openai-api-key=$OPENAI_API_KEY")
BACKEND_ENV_VARS=(
  "OPENAI_API_KEY=secretref:openai-api-key"
  "OPENAI_MODEL=$OPENAI_MODEL"
  "STORAGE_ACCOUNT_URL=$STORAGE_ACCOUNT_URL"
  "ADLS_FILESYSTEM=$ADLS_FILESYSTEM"
)
if [ -n "$ADLS_SAS_TOKEN" ]; then
  BACKEND_SECRETS+=("adls-sas-token=$ADLS_SAS_TOKEN")
  BACKEND_ENV_VARS+=("ADLS_SAS_TOKEN=secretref:adls-sas-token")
fi

_upsert_containerapp "$BACKEND_APP" \
  --environment "$ENVIRONMENT" \
  --image "$ACR_SERVER/$BACKEND_IMAGE" \
  --registry-server "$ACR_SERVER" \
  --registry-username "$ACR_NAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8000 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --secrets "${BACKEND_SECRETS[@]}" \
  --env-vars "${BACKEND_ENV_VARS[@]}"

BACKEND_FQDN=$(az containerapp show \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo "✓ Backend deployed (internal): https://$BACKEND_FQDN"

# ── 6. Deploy frontend (external ingress — public demo URL) ───────────────────
echo "==> Deploying frontend..."
_upsert_containerapp "$FRONTEND_APP" \
  --environment "$ENVIRONMENT" \
  --image "$ACR_SERVER/$FRONTEND_IMAGE" \
  --registry-server "$ACR_SERVER" \
  --registry-username "$ACR_NAME" \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8501 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
      "BACKEND_URL=https://$BACKEND_FQDN"

FRONTEND_FQDN=$(az containerapp show \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "════════════════════════════════════════════════════════"
echo "  EDAta is live!"
echo ""
echo "  Demo URL  : https://$FRONTEND_FQDN"
echo "  API docs  : https://$BACKEND_FQDN/docs  (internal)"
echo "════════════════════════════════════════════════════════"

# ── Teardown reminder ─────────────────────────────────────────────────────────
echo ""
echo "To tear down after the demo:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
