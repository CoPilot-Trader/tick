"""
Signal Bridge API Router.

Serves external signal datasets (Level Rejection, PCR Shock) from
Tory's GCS pipeline. Data is loaded from local JSON files under
storage/signal_data/ and cached in memory. A refresh endpoint can
re-download from GCS when new data is available.

Level Rejection uses the raw per-signal feed at
`gs://copilot-ai-trader-data/briefings/signals_raw/level_rejection/` (per
Tory's 2026-07-08 handoff — supersedes the April-dead `copilot-signal-bridge`
bucket). Hit flags in that feed are tri-state (1/0/null) — see _is_hit().
PCR_SHOCK is a separate dataset with its own schema; kept on the legacy
path until Tory publishes a repoint for that lane.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/signals", tags=["Signal Bridge"])

SIGNAL_DATA_DIR = Path(__file__).parent.parent.parent / "storage" / "signal_data"

# ── In-memory caches ─────────────────────────────────────────────
_level_rejection_cache: Optional[List[Dict]] = None
_pcr_shock_cache: Optional[List[Dict]] = None

# Live bucket for the raw Level Rejection per-signal feed.
GCS_BUCKET = "copilot-ai-trader-data"
GCS_LR_KEY = "briefings/signals_raw/level_rejection/level_rejection_latest.json"
# PCR_SHOCK is on a separate dataset Tory hasn't repointed yet — legacy path
# still applies (was last written 2026-05-16). Kept read-only until repoint.
GCS_PCR_BUCKET = "copilot-signal-bridge"
GCS_PCR_KEY = "exports/pcr_shock_forecast_v1.json"


def _is_hit(v: Any) -> bool:
    """Tri-state hit flag: 1=hit, 0=not-hit, null/None=pending.
    Only 1 counts as a real hit — never conflate pending with a miss.
    """
    return v == 1


def _load_level_rejection() -> List[Dict]:
    global _level_rejection_cache
    if _level_rejection_cache is not None:
        return _level_rejection_cache
    path = SIGNAL_DATA_DIR / "level_rejection_calls_v1.json"
    if not path.exists():
        logger.warning("Level rejection data file not found: %s", path)
        _level_rejection_cache = []
        return _level_rejection_cache
    _level_rejection_cache = json.loads(path.read_text())
    logger.info("Loaded %d level rejection signals", len(_level_rejection_cache))
    return _level_rejection_cache


def _load_pcr_shock() -> List[Dict]:
    global _pcr_shock_cache
    if _pcr_shock_cache is not None:
        return _pcr_shock_cache
    path = SIGNAL_DATA_DIR / "pcr_shock_forecast_v1.json"
    if not path.exists():
        logger.warning("PCR shock data file not found: %s", path)
        _pcr_shock_cache = []
        return _pcr_shock_cache
    _pcr_shock_cache = json.loads(path.read_text())
    logger.info("Loaded %d PCR shock signals", len(_pcr_shock_cache))
    return _pcr_shock_cache


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/health")
async def health():
    lr = _load_level_rejection()
    pcr = _load_pcr_shock()
    return {
        "status": "healthy",
        "datasets": {
            "level_rejection": {"count": len(lr), "file": str(SIGNAL_DATA_DIR / "level_rejection_calls_v1.json")},
            "pcr_shock": {"count": len(pcr), "file": str(SIGNAL_DATA_DIR / "pcr_shock_forecast_v1.json")},
        },
    }


@router.get("/level-rejection/{ticker}")
async def get_level_rejection(
    ticker: str,
    start: Optional[str] = Query(None, description="ISO start date filter"),
    end: Optional[str] = Query(None, description="ISO end date filter"),
) -> Dict[str, Any]:
    """Return Level Rejection signals for a ticker, optionally filtered by date range."""
    all_signals = _load_level_rejection()
    filtered = [s for s in all_signals if s.get("ticker", "").upper() == ticker.upper()]

    if start:
        filtered = [s for s in filtered if s.get("signal_time", "") >= start]
    if end:
        filtered = [s for s in filtered if s.get("signal_time", "") <= end]

    filtered.sort(key=lambda s: s.get("signal_time", ""))

    # Aggregate win rate. Trust Tory's derived `outcome_filled` — some rows
    # carry a stale DB "evaluated" flag but have null hit data, and the
    # derived flag correctly categorises those as pending. Only count 1 as
    # a hit; null (pending) must never be conflated with 0 (miss).
    resolved = [s for s in filtered if s.get("outcome_filled")]
    pending = [s for s in filtered if not s.get("outcome_filled")]
    wins = sum(1 for s in resolved if _is_hit(s.get("target1_hit")))
    win_rate = round(wins / len(resolved), 3) if resolved else None

    return {
        "status": "success",
        "ticker": ticker.upper(),
        "count": len(filtered),
        "resolved_count": len(resolved),
        "pending_count": len(pending),
        "win_rate": win_rate,
        "signals": filtered,
    }


@router.get("/pcr-shock/{ticker}")
async def get_pcr_shock(
    ticker: str,
    start: Optional[str] = Query(None, description="ISO start date filter"),
    end: Optional[str] = Query(None, description="ISO end date filter"),
) -> Dict[str, Any]:
    """Return raw PCR Shock signals for a ticker."""
    all_signals = _load_pcr_shock()
    filtered = [s for s in all_signals if s.get("ticker", "").upper() == ticker.upper()]

    if start:
        filtered = [s for s in filtered if s.get("signal_ts", "") >= start]
    if end:
        filtered = [s for s in filtered if s.get("signal_ts", "") <= end]

    filtered.sort(key=lambda s: s.get("signal_ts", ""))

    return {
        "status": "success",
        "ticker": ticker.upper(),
        "count": len(filtered),
        "signals": filtered,
    }


@router.get("/pcr-shock/{ticker}/backtrack")
async def get_pcr_shock_backtrack(
    ticker: str,
    limit: int = Query(500, ge=1, le=2000),
) -> Dict[str, Any]:
    """
    Return PCR Shock signals reshaped into the same PredictionHistoryEntry
    format used by /api/v1/forecast/{ticker}/history so they merge into
    the existing Predicted-vs-Actual panel.
    """
    all_signals = _load_pcr_shock()
    filtered = [s for s in all_signals if s.get("ticker", "").upper() == ticker.upper()]
    filtered.sort(key=lambda s: s.get("signal_ts", ""))
    filtered = filtered[-limit:]

    predictions = []
    resolved_count = 0
    total_error = 0.0
    correct_dir = 0

    for s in filtered:
        spot = s.get("spot_at_signal")
        if not spot:
            continue

        sig_type = s.get("signal_type", "")
        # Derive direction from signal type
        if "DROP" in sig_type.upper():
            direction = "DOWN"
            implied_move = -0.005  # -0.5% expected
        elif "SPIKE" in sig_type.upper():
            direction = "UP"
            implied_move = 0.005
        else:
            direction = "UP"
            implied_move = 0.003

        predicted_price = round(spot * (1 + implied_move), 2)

        # Confidence from outcome_class
        oc = s.get("outcome_class")
        if oc == "STRONG_WIN":
            confidence = 0.9
        elif oc == "WIN":
            confidence = 0.75
        elif oc == "FLAT":
            confidence = 0.5
        elif oc == "LOSS":
            confidence = 0.4
        else:
            confidence = 0.6

        # Actual price from fwd_1d_pct
        fwd_1d = s.get("fwd_1d_pct")
        if fwd_1d is not None:
            actual_price = round(spot * (1 + fwd_1d / 100), 2)
            error_pct = round(abs(predicted_price - actual_price) / spot * 100, 4)
            actual_dir = "UP" if actual_price >= spot else "DOWN"
            dir_correct = actual_dir == direction
            resolved_count += 1
            total_error += error_pct
            if dir_correct:
                correct_dir += 1
        else:
            actual_price = None
            error_pct = None
            dir_correct = None

        # Parse signal_ts to compute target_date
        try:
            ts = datetime.fromisoformat(s["signal_ts"].replace("Z", "+00:00"))
            target_dt = ts + timedelta(days=1)
            target_date = target_dt.strftime("%Y-%m-%d")
            target_timestamp = target_dt.isoformat()
        except Exception:
            target_date = s.get("signal_ts", "")[:10]
            target_timestamp = None

        predictions.append({
            "predicted_at": s["signal_ts"],
            "horizon": "1d",
            "base_price": spot,
            "predicted_price": predicted_price,
            "confidence": confidence,
            "direction": direction,
            "target_date": target_date,
            "target_timestamp": target_timestamp,
            "actual_price": actual_price,
            "error_pct": error_pct,
            "direction_correct": dir_correct,
            "source": "pcr_shock",
        })

    # Accuracy stats
    if resolved_count > 0:
        accuracy = {
            "mape": round(total_error / resolved_count, 2),
            "directional_accuracy": round(correct_dir / resolved_count * 100, 1),
            "total_predictions": len(predictions),
            "resolved": resolved_count,
        }
    else:
        accuracy = None

    return {
        "status": "success",
        "symbol": ticker.upper(),
        "count": len(predictions),
        "predictions": predictions,
        "accuracy": accuracy,
    }


@router.post("/refresh")
async def refresh_from_gcs() -> Dict[str, Any]:
    """Re-download signal data from GCS. Requires google-cloud-storage.

    Level Rejection reads from the new `copilot-ai-trader-data` bucket at
    `briefings/signals_raw/level_rejection/level_rejection_latest.json`.
    PCR_SHOCK stays on the legacy bucket until Tory publishes a repoint —
    a 404 there is expected and non-fatal.
    """
    global _level_rejection_cache, _pcr_shock_cache
    try:
        from google.cloud import storage as gcs_storage

        client = gcs_storage.Client()

        SIGNAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        downloaded = []
        skipped = []

        for bucket_name, gcs_key, local_name in [
            (GCS_BUCKET, GCS_LR_KEY, "level_rejection_calls_v1.json"),
            (GCS_PCR_BUCKET, GCS_PCR_KEY, "pcr_shock_forecast_v1.json"),
        ]:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(gcs_key)
            if blob.exists():
                dest = SIGNAL_DATA_DIR / local_name
                blob.download_to_filename(str(dest))
                downloaded.append(local_name)
                logger.info("Downloaded gs://%s/%s -> %s", bucket_name, gcs_key, local_name)
            else:
                skipped.append(f"gs://{bucket_name}/{gcs_key}")
                logger.warning("GCS blob not found: gs://%s/%s", bucket_name, gcs_key)

        # Clear caches so next request reloads from disk
        _level_rejection_cache = None
        _pcr_shock_cache = None

        return {
            "status": "success",
            "downloaded": downloaded,
            "skipped": skipped,
            "message": f"Refreshed {len(downloaded)} file(s) from GCS",
        }

    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="google-cloud-storage not installed. Install it to use GCS refresh.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS refresh failed: {e}")
