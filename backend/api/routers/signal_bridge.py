"""
Signal Bridge API Router.

Serves external signal datasets (Level Rejection, PCR Shock) from
Tory's GCS pipeline. Data is loaded from local JSON files under
storage/signal_data/ and cached in memory. A refresh endpoint can
re-download from GCS when new data is available.
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

GCS_BUCKET = "copilot-signal-bridge"
GCS_LR_KEY = "exports/level_rejection_calls_v1.json"
GCS_PCR_KEY = "exports/pcr_shock_forecast_v1.json"


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

    # Aggregate win rate
    outcomes = [s for s in filtered if s.get("outcome_filled")]
    wins = sum(1 for s in outcomes if s.get("target1_hit"))
    win_rate = round(wins / len(outcomes), 3) if outcomes else None

    return {
        "status": "success",
        "ticker": ticker.upper(),
        "count": len(filtered),
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
    """Re-download signal data from GCS. Requires google-cloud-storage."""
    global _level_rejection_cache, _pcr_shock_cache
    try:
        from google.cloud import storage as gcs_storage

        client = gcs_storage.Client()
        bucket = client.bucket(GCS_BUCKET)

        SIGNAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        downloaded = []

        for gcs_key, local_name in [
            (GCS_LR_KEY, "level_rejection_calls_v1.json"),
            (GCS_PCR_KEY, "pcr_shock_forecast_v1.json"),
        ]:
            blob = bucket.blob(gcs_key)
            if blob.exists():
                dest = SIGNAL_DATA_DIR / local_name
                blob.download_to_filename(str(dest))
                downloaded.append(local_name)
                logger.info("Downloaded %s from GCS", local_name)
            else:
                logger.warning("GCS blob %s not found", gcs_key)

        # Clear caches so next request reloads from disk
        _level_rejection_cache = None
        _pcr_shock_cache = None

        return {
            "status": "success",
            "downloaded": downloaded,
            "message": f"Refreshed {len(downloaded)} file(s) from GCS",
        }

    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="google-cloud-storage not installed. Install it to use GCS refresh.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS refresh failed: {e}")
