#!/usr/bin/env bash
#
# Deploy the TICK HTML report suite to Google Cloud Run.
#
# Usage:
#   cd reports
#   ./deploy.sh                         # uses gcloud's active project
#   GCP_PROJECT=my-project ./deploy.sh  # override project
#   REGION=europe-west1 ./deploy.sh     # override region (default: us-central1)
#   SERVICE=tick-reports ./deploy.sh    # override service name
#
# Requirements:
#   * gcloud CLI installed and authenticated (`gcloud auth login`)
#   * A GCP project with billing enabled and Cloud Run + Cloud Build APIs on
#
# The script uses `gcloud run deploy --source .` so you don't need Docker
# locally — Cloud Build performs the image build for you.

set -euo pipefail

SERVICE="${SERVICE:-tick-reports}"
REGION="${REGION:-us-central1}"
GCP_PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null || true)}"

if [[ -z "${GCP_PROJECT}" ]]; then
  echo "❌ No GCP project set. Run: gcloud config set project YOUR-PROJECT-ID"
  exit 1
fi

echo "=== TICK Reports · Cloud Run Deploy ==="
echo "  Project: ${GCP_PROJECT}"
echo "  Region:  ${REGION}"
echo "  Service: ${SERVICE}"
echo

# Enable required APIs (idempotent — safe to re-run).
echo "→ Ensuring Cloud Run & Cloud Build APIs are enabled..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  --project "${GCP_PROJECT}" --quiet

echo "→ Deploying (this triggers a Cloud Build image build)..."
gcloud run deploy "${SERVICE}" \
  --project "${GCP_PROJECT}" \
  --region "${REGION}" \
  --source . \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 256Mi \
  --max-instances 5 \
  --min-instances 0 \
  --port 8080 \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" \
  --project "${GCP_PROJECT}" \
  --region "${REGION}" \
  --format='value(status.url)')"

echo
echo "✅ Deploy complete."
echo "   Hub:       ${URL}/"
echo "   Master:    ${URL}/tick-delivery-report.html"
echo "   Milestone: ${URL}/milestones/m5-summary.html"
echo
echo "Share the hub URL with the client — no authentication required."
