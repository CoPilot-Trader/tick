# Signal Bridge Integration — TICK ↔ Platform Signal Feeds

**Audience:** Any dev on the platform side taking over signal publishing to TICK.
**Last updated:** 2026-07-08

TICK's charts and signal log consume external trading signals produced by
Tory's platform pipeline. This document covers the contract between the two
systems: what TICK reads, where it reads it from, how it refreshes, and how
to add a new signal source.

---

## 1. Datasets in play

| Dataset | Purpose in TICK | Status |
|---|---|---|
| **Level Rejection** | Rendered as trade signals on the chart (entry / target / stop lines + W/L/pending markers) and in the Signals Log side panel | **Live** on new bucket (see below) |
| **PCR Shock** | Reshaped as prediction backtracks in the Predicted-vs-Actual side panel | **Legacy** — separate feed, awaits Tory's repoint |

---

## 2. Level Rejection — live path

### 2.1 Bucket + object

```
gs://copilot-ai-trader-data/briefings/signals_raw/level_rejection/level_rejection_latest.json
```

Companion files under the same prefix that TICK does **not** currently consume
but are safe to write:

| File | Purpose |
|---|---|
| `level_rejection_<timestamp>.json` | Dated snapshot for history / audit |
| `_manifest.json` | Heartbeat — should include `last_run_utc`, `row_count`, `pending_count` for staleness detection |

### 2.2 Access

- **Service account** (TICK backend): `374752069232-compute@developer.gserviceaccount.com`
- **Required grant**: `roles/storage.objectViewer` on the `briefings/` prefix (or the whole bucket).
- One-time IAM binding; no per-file grant needed.

### 2.3 Schema — one record per signal

`List[Dict]` at the JSON root. Field order in the raw file is not enforced.

| field | type | notes |
|---|---|---|
| `ticker` | string | e.g. `AAPL`, `MU` |
| `signal_time` | ISO8601 with tz offset | ET offset, e.g. `-04:00` |
| `level_type` | string | e.g. `SESSION_VWAP`, `PDL_resist` |
| `side` | string | `CALL` or `PUT` |
| `entry_price` | float | |
| `spot_at_signal` | float | Alias of `entry_price` — kept for compatibility |
| `target1_price` | float | |
| `target1_hit` | `1` \| `0` \| `null` | **Tri-state.** `null` = pending, don't treat as miss |
| `target2_price` | float | Second target ladder |
| `target2_hit` | `1` \| `0` \| `null` | Tri-state, same rules |
| `stop_price` | float | |
| `stop_hit` | `1` \| `0` \| `null` | Tri-state |
| `outcome_filled` | bool | Derived — trust this over any raw DB flag |

**Example — resolved signal:**
```json
{
  "ticker": "MU",
  "signal_time": "2026-07-01T10:42:03.047507-04:00",
  "level_type": "SESSION_VWAP", "side": "CALL",
  "spot_at_signal": 1082.99, "entry_price": 1082.99,
  "target1_price": 1129.86, "target1_hit": 1,
  "target2_price": 1129.99, "target2_hit": 0,
  "stop_price": 1078.61, "stop_hit": 0,
  "outcome_filled": true
}
```

**Example — pending signal (all hit flags null):**
```json
{
  "ticker": "PLTR",
  "signal_time": "2026-07-08T09:52:03.469784-04:00",
  "level_type": "PDL_resist", "side": "PUT",
  "spot_at_signal": 131.03, "entry_price": 131.03,
  "target1_price": 129.38, "target1_hit": null,
  "target2_price": 129.0, "target2_hit": null,
  "stop_price": 131.72, "stop_hit": null,
  "outcome_filled": false
}
```

### 2.4 Semantics TICK enforces

- **`target1_hit == 1`** → win (green marker)
- **`stop_hit == 1`** → loss (red marker)
- **`outcome_filled == false`** → pending (gray marker, no W/L attribution)
- **`target1_hit == null`** is never counted as `0`. Any code that treats
  null as false is a bug; upstream must emit true `null`, not `0`.

### 2.5 Recommended write cadence

Twice daily, shortly after the platform briefing refresh, **Mon–Fri**, plus
a weekend snapshot. Rationale: outcome flags need overnight for the tracker
to fill. TICK's cache TTL (see §4) is short enough to pick up within a
minute of the write.

---

## 3. PCR Shock — legacy path (awaits repoint)

Not migrated as of this doc. TICK still reads from the pre-migration
bucket. Path in code:

```python
GCS_PCR_BUCKET = "copilot-signal-bridge"
GCS_PCR_KEY = "exports/pcr_shock_forecast_v1.json"
```

Schema differs — no entry/target/stop/level fields; carries forward-return
percentages instead. TICK converts these into `PredictionHistoryEntry`
records for the Predicted-vs-Actual panel. If PCR is repointed, either:

1. Publish to `gs://copilot-ai-trader-data/briefings/signals_raw/pcr_shock/pcr_shock_latest.json` — TICK will need a two-line config change (see §5.1), OR
2. Publish under a new bucket entirely — update both `GCS_PCR_BUCKET` and `GCS_PCR_KEY`.

The internal `signal_ts`, `outcome_class`, `fwd_1d_pct`, `signal_type`,
`spot_at_signal` fields must stay the same shape.

---

## 4. How TICK refreshes

- **Storage layer:** files land under `backend/storage/signal_data/` inside the container.
- **In-memory cache:** loaded on first request per file, held for the process lifetime.
- **HTTP cache** (Redis): OHLCV bar cache — 60s intraday, 300s daily+. Signal endpoints are not Redis-cached (they read the in-memory copy directly).
- **Refresh trigger:** `POST /api/v1/signals/refresh` re-downloads both feeds from GCS and clears the in-memory cache. No auto-poll; wire it to a cron / cloud function on your side if you want fully automatic refresh.

### 4.1 Refresh via HTTP

```bash
curl -X POST http://<tick-host>:8000/api/v1/signals/refresh
# → { "status": "success", "downloaded": ["level_rejection_calls_v1.json"], "skipped": ["gs://copilot-signal-bridge/exports/pcr_shock_forecast_v1.json"], ... }
```

### 4.2 Health check

```bash
curl http://<tick-host>:8000/api/v1/signals/health
# → { "status": "healthy", "datasets": { "level_rejection": { "count": 3539, ... } } }
```

---

## 5. File-by-file map for TICK's signal integration

| File | Purpose |
|---|---|
| `backend/api/routers/signal_bridge.py` | HTTP endpoints, GCS refresh, tri-state hit logic |
| `backend/storage/signal_data/level_rejection_calls_v1.json` | Local mirror of the raw feed (rewritten by refresh) |
| `backend/storage/signal_data/pcr_shock_forecast_v1.json` | Legacy PCR mirror |
| `frontend/src/types/index.ts` — `LevelRejectionSignal` | Type contract (tri-state fields marked) |
| `frontend/src/components/SignalsLog.tsx` — `SignalRow` | Renders one signal card; handles pending state |
| `frontend/src/components/CandlestickChart.tsx` — level rejection block | Draws entry/target/stop price lines + W/L/pending markers |

### 5.1 Changing a bucket / object path

All bucket + key constants live at the top of `signal_bridge.py`:

```python
GCS_BUCKET = "copilot-ai-trader-data"
GCS_LR_KEY = "briefings/signals_raw/level_rejection/level_rejection_latest.json"
GCS_PCR_BUCKET = "copilot-signal-bridge"
GCS_PCR_KEY = "exports/pcr_shock_forecast_v1.json"
```

Change these, restart the backend container, hit `/refresh`. No frontend
changes needed.

---

## 6. Adding a new signal source (e.g. news alerts, options flow)

Follow the pattern of Level Rejection:

1. **Backend** — in `signal_bridge.py`:
   - Add constants: bucket, key, in-memory cache variable.
   - Add a `_load_<name>()` loader function.
   - Add a GET endpoint: `/api/v1/signals/<name>/{ticker}`.
   - Add the bucket + key to the loop in `refresh_from_gcs()`.
2. **Frontend types** — add an interface to `types/index.ts` and a fetcher method to `client.ts`.
3. **UI** — either render in `SignalsLog.tsx` (new source in the union type) or as an overlay on the chart in `CandlestickChart.tsx`.

Tri-state hit semantics from §2.4 apply to any outcome-tracked signal.

---

## 7. Troubleshooting

| Symptom | Likely cause | Where to look |
|---|---|---|
| Signals log empty | GCS bucket has no writer, or wrong key | `POST /refresh` and read the `skipped` array in the response |
| Chart shows pending signals as loss (red L) | Consumer treating `null` hit as `0` | Search for `.target1_hit` — every check should be `=== 1` or `=== 0`, never truthy/falsy |
| Old signals still showing after re-publish | In-memory cache; container restart or `/refresh` needed | `docker compose restart backend` or `POST /refresh` |
| GCS auth error on `/refresh` | Service account missing `objectViewer` on target prefix | Confirm binding in the target project's IAM |
| PCR panel shows April data | PCR bucket hasn't been repointed | Update `GCS_PCR_BUCKET` / `GCS_PCR_KEY` per §3 |

---

## 8. Contact

- **TICK integration questions:** owner listed in `README.md` / `TEAM.md`.
- **Platform-side feed schema questions:** Tory (VM side).

*This doc is versioned in the TICK repo at `docs/SIGNAL_BRIDGE_INTEGRATION.md`. Update it here when the contract changes.*
