# TICK marketing

Public-facing marketing site for the TICK multi-agent stock prediction
platform. Runs as a separate container in the local compose stack and is
intended for Cloud Run as the standalone front door.

## Local

```sh
# from repo root
docker compose up marketing
# → http://localhost:3002
```

The site server-fetches live OHLCV from the `backend` service on the
docker network. Outside compose, set `NEXT_PUBLIC_API_URL` and
`TICK_INTERNAL_API_URL` to your backend host (e.g. `http://localhost:8000`).

## Standalone dev

```sh
cd marketing
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 \
TICK_INTERNAL_API_URL=http://localhost:8000 \
NEXT_PUBLIC_DASHBOARD_URL=http://localhost:3000 \
npm run dev
```

## Cloud Run

The Dockerfile produces a `node:20-alpine` standalone image listening on
`PORT=3002`. Cloud Run will inject its own `PORT`; the runner respects it.
At deploy time set:

- `NEXT_PUBLIC_API_URL` — public API URL (e.g. `https://api.tick.trade`)
- `TICK_INTERNAL_API_URL` — same as public on Cloud Run (no compose net)
- `NEXT_PUBLIC_DASHBOARD_URL` — public dashboard URL

## Sections

`AppBar → TickerStrip → Hero → Problem → Showcase → Strategies →
HowItWorks → Democratization → AccuracyStats → Pricing → CTA → Footer`
