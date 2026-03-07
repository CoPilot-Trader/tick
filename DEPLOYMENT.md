# TICK Platform - GCP Deployment Guide

Deploy the full TICK stack (TimescaleDB, Redis, FastAPI backend, Next.js frontend) on a single GCP Compute Engine VM using Docker Compose.

## Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed locally ([install guide](https://cloud.google.com/sdk/docs/install))
- Project created in GCP Console

## 1. Create a GCP VM

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create a VM (e2-medium is sufficient for demo/testing)
gcloud compute instances create tick-server \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server

# Open ports 3000 (frontend) and 8000 (backend API)
gcloud compute firewall-rules create allow-tick-ports \
  --allow=tcp:3000,tcp:8000 \
  --target-tags=http-server \
  --description="Allow TICK frontend and backend"
```

## 2. SSH into the VM

```bash
gcloud compute ssh tick-server --zone=us-central1-a
```

## 3. Install Docker & Docker Compose on the VM

```bash
# Install Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to docker group (avoids needing sudo)
sudo usermod -aG docker $USER
newgrp docker
```

## 4. Clone the Repository

```bash
git clone https://github.com/CoPilot-Trader/tick.git
cd tick
git checkout feature/level-detection
```

## 5. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit with your actual API keys
nano .env
```

Fill in the `.env` file:

```env
# News APIs (already provided)
FINNHUB_API_KEY=your_finnhub_key
NEWSAPI_KEY=your_newsapi_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Market data
TIINGO_API_KEY=your_tiingo_key
FMP_API_KEY=your_fmp_key

# LLM Sentiment (optional - mock fallback if not set)
OPENAI_API_KEY=your_openai_key

# Database
POSTGRES_USER=tick_user
POSTGRES_PASSWORD=CHANGE_THIS_TO_A_STRONG_PASSWORD
POSTGRES_DB=tick_db

# Frontend API URL - use your VM's external IP
NEXT_PUBLIC_API_URL=http://YOUR_VM_EXTERNAL_IP:8000
```

Get your VM's external IP:
```bash
curl -s ifconfig.me
```

## 6. Deploy with Docker Compose

```bash
# Build and start all services (production mode)
docker compose -f docker-compose.prod.yml up -d --build

# Watch the logs to verify everything starts
docker compose -f docker-compose.prod.yml logs -f
```

Wait for all services to show healthy:
- `tick-db`: TimescaleDB ready
- `tick-redis`: Redis ready
- `tick-backend`: Uvicorn running on 0.0.0.0:8000
- `tick-frontend`: Next.js production server on port 3000

## 7. Verify the Deployment

```bash
# Check all containers are running
docker compose -f docker-compose.prod.yml ps

# Test backend health
curl http://localhost:8000/health

# Test sentiment pipeline health
curl http://localhost:8000/api/v1/sentiment/health

# Test live news fetch
curl "http://localhost:8000/api/v1/sentiment/news/AAPL?days=7&max_articles=5"

# Test full sentiment pipeline
curl "http://localhost:8000/api/v1/sentiment/AAPL?time_horizon=1d"

# Test fusion signal
curl "http://localhost:8000/api/v1/fusion/AAPL?time_horizon=1d"
```

Access the dashboard: `http://YOUR_VM_EXTERNAL_IP:3000`

## 8. Common Operations

### View logs
```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Restart a service
```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Update to latest code
```bash
git pull origin feature/level-detection
docker compose -f docker-compose.prod.yml up -d --build
```

### Stop everything
```bash
docker compose -f docker-compose.prod.yml down
```

### Stop and remove data volumes
```bash
docker compose -f docker-compose.prod.yml down -v
```

## Architecture on GCP

```
GCP Compute Engine (e2-medium)
├── Docker Compose
│   ├── tick-db       (TimescaleDB on port 5433)
│   ├── tick-redis    (Redis on port 6380)
│   ├── tick-backend  (FastAPI on port 8000)  ← Live news + sentiment
│   └── tick-frontend (Next.js on port 3000)  ← Dashboard
└── External access: ports 3000, 8000
```

## Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `FINNHUB_API_KEY` | Yes | Finnhub stock news API |
| `NEWSAPI_KEY` | Yes | NewsAPI general news |
| `ALPHA_VANTAGE_API_KEY` | Yes | Alpha Vantage financial news |
| `TIINGO_API_KEY` | No | Tiingo market data |
| `FMP_API_KEY` | No | Financial Modeling Prep |
| `OPENAI_API_KEY` | No | GPT-4 sentiment analysis (falls back to mock) |
| `POSTGRES_PASSWORD` | Yes | Database password (change default!) |
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL for frontend (use VM external IP) |

## Troubleshooting

**Backend won't start**: Check logs with `docker compose -f docker-compose.prod.yml logs backend`. Common issues: database not ready yet (wait for healthcheck), missing Python dependencies.

**Frontend shows "Failed to fetch"**: The `NEXT_PUBLIC_API_URL` must be set to `http://YOUR_EXTERNAL_IP:8000` (not localhost) so the browser can reach the backend.

**News returns mock data**: Verify API keys are set in `.env` and the backend container received them: `docker exec tick-backend env | grep API_KEY`.

**Sentiment returns all neutral**: Without `OPENAI_API_KEY`, the system uses mock sentiment which generates weak scores. Set the key for real GPT-4 analysis.

**Prophet model takes long to load**: First prediction request may take 30-60s as Prophet trains on historical data. Subsequent requests are faster due to model caching.
