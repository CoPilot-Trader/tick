# TICK Platform - GCP Deployment Guide

Deploy the full TICK stack (TimescaleDB, Redis, FastAPI backend, Next.js frontend) on a single GCP Compute Engine VM using Docker Compose.

> This guide was tested on 2026-03-09 using GCP project `copilot-ai-trader`.

## Prerequisites

- GCP account with billing enabled
- Access to GCP Cloud Shell (built into GCP Console — click the terminal icon top-right)

## Step 1: Set Project & Create VM

Open **GCP Cloud Shell** from the Console, then:

```bash
# Set project
gcloud config set project copilot-ai-trader

# Create VM (e2-medium: 2 vCPU, 4GB RAM — sufficient for demo/testing)
gcloud compute instances create tick-server \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server

# Open firewall ports for frontend (3000) and backend API (8000)
gcloud compute firewall-rules create allow-tick-ports \
  --allow=tcp:3000,tcp:8000 \
  --target-tags=http-server \
  --description="Allow TICK frontend and backend"
```

Note the `EXTERNAL_IP` from the output — you'll need it later.

## Step 2: SSH into the VM

```bash
gcloud compute ssh tick-server --zone=us-central1-a
```

## Step 3: Install Docker (inside VM)

Run as one block:

```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg && \
sudo install -m 0755 -d /etc/apt/keyrings && \
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
sudo chmod a+r /etc/apt/keyrings/docker.gpg && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && \
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin && \
sudo usermod -aG docker $USER && \
newgrp docker
```

## Step 4: Clone & Configure

```bash
git clone https://github.com/CoPilot-Trader/tick.git && cd tick && git checkout feature/level-detection
```

Create the `.env` file (replace `EXTERNAL_IP` with your VM's IP from Step 1):

```bash
EXTERNAL_IP=$(curl -s ifconfig.me)

cat > .env << EOF
FINNHUB_API_KEY=d5d3rmpr01qvl80nhh40d5d3rmpr01qvl80nhh4g
NEWSAPI_KEY=6fd53b5d6c584a2d9052bcf48988d9be
ALPHA_VANTAGE_API_KEY=2JSGRZ6R9VRMW7OL
TIINGO_API_KEY=9e7e7ef41ad8cefe4bfa3f57e7bb60b5d81e3d14
FMP_API_KEY=W8Qj3LfEWEh5EGBo8gBlCQ4QNT36rZ8j
OPENAI_API_KEY=
POSTGRES_USER=tick_user
POSTGRES_PASSWORD=tick_password
POSTGRES_DB=tick_db
NEXT_PUBLIC_API_URL=http://${EXTERNAL_IP}:8000
EOF

echo "Dashboard will be at: http://${EXTERNAL_IP}:3000"
```

## Step 5: Deploy

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First build takes ~7 minutes (Prophet, numpy, Next.js build). Watch progress:

```bash
docker compose -f docker-compose.prod.yml logs -f
```

(Press Ctrl+C to exit logs — containers keep running.)

## Step 6: Verify

```bash
# All 4 containers should show "Up" / "healthy"
docker compose -f docker-compose.prod.yml ps

# Backend health check
curl http://localhost:8000/health

# Test live news from all 3 sources
curl "http://localhost:8000/api/v1/sentiment/news/AAPL?days=7&max_articles=5"

# Test full sentiment pipeline
curl "http://localhost:8000/api/v1/sentiment/AAPL?time_horizon=1d"
```

Dashboard: `http://YOUR_EXTERNAL_IP:3000`

## Day-to-Day Operations

### View logs
```bash
docker compose -f docker-compose.prod.yml logs -f backend    # backend only
docker compose -f docker-compose.prod.yml logs -f             # all services
```

### Restart after code update
```bash
cd ~/tick
git pull origin feature/level-detection
docker compose -f docker-compose.prod.yml up -d --build
```

### Restart a single service
```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Stop everything
```bash
docker compose -f docker-compose.prod.yml down
```

### Check env vars are loaded
```bash
docker exec tick-backend env | grep -E "FINNHUB|NEWSAPI|ALPHA_VANTAGE|OPENAI|TIINGO|FMP"
```

### Add OpenAI key later
```bash
cd ~/tick
nano .env                # add OPENAI_API_KEY=sk-...
docker compose -f docker-compose.prod.yml restart backend
```

## Architecture

```
GCP Compute Engine (e2-medium, us-central1-a)
├── Docker Compose (docker-compose.prod.yml)
│   ├── tick-db        TimescaleDB     :5433
│   ├── tick-redis     Redis           :6380
│   ├── tick-backend   FastAPI/Uvicorn :8000  ← Live news + sentiment + fusion
│   └── tick-frontend  Next.js         :3000  ← Dashboard UI
├── .env               API keys + config
└── Firewall: ports 3000, 8000 open
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FINNHUB_API_KEY` | Yes | Finnhub stock news API |
| `NEWSAPI_KEY` | Yes | NewsAPI general news aggregation |
| `ALPHA_VANTAGE_API_KEY` | Yes | Alpha Vantage financial news |
| `TIINGO_API_KEY` | No | Tiingo market data |
| `FMP_API_KEY` | No | Financial Modeling Prep |
| `OPENAI_API_KEY` | No | GPT-4 sentiment (falls back to keyword-based mock) |
| `POSTGRES_PASSWORD` | Yes | Database password |
| `NEXT_PUBLIC_API_URL` | Yes | Backend URL for frontend (must use external IP) |

## Troubleshooting

**Containers won't start:** Check `docker compose -f docker-compose.prod.yml logs backend`. Usually TimescaleDB healthcheck hasn't passed yet — wait 15s and retry.

**Frontend shows "Failed to fetch":** `NEXT_PUBLIC_API_URL` must be `http://EXTERNAL_IP:8000` (not `localhost`). The browser makes requests from the user's machine, not the VM.

**News returns mock data:** Run `docker exec tick-backend env | grep API_KEY` to verify keys are loaded. If empty, check root `.env` file exists (not just `backend/.env`).

**Sentiment returns neutral/zero:** Without `OPENAI_API_KEY`, mock sentiment generates weak scores. Set the key and restart backend for real GPT-4 analysis.

**Prophet slow on first request:** First prediction takes 30-60s as Prophet trains on historical data. Subsequent requests use cached models.

**VM costs:** e2-medium costs ~$25/month. Stop the VM when not in use: `gcloud compute instances stop tick-server --zone=us-central1-a`. Start it back: `gcloud compute instances start tick-server --zone=us-central1-a` (external IP may change — update `.env`).
