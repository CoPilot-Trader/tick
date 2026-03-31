"""
Real-time price streaming via WebSocket.

Provides live price updates for the frontend chart.
Fetches latest candle data every few seconds and pushes to connected clients.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.data_agent.agent import DataAgent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Streaming"])

_data_agent: Optional[DataAgent] = None


def get_data_agent() -> DataAgent:
    global _data_agent
    if _data_agent is None:
        _data_agent = DataAgent()
        _data_agent.initialize()
    return _data_agent


# Track active WebSocket connections per symbol
active_connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/ws/stream/{symbol}")
async def stream_price(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time price streaming.

    Sends latest OHLCV candle data every 5 seconds.
    Client receives JSON messages with candle updates.
    """
    await websocket.accept()

    symbol = symbol.upper()
    if symbol not in active_connections:
        active_connections[symbol] = set()
    active_connections[symbol].add(websocket)

    logger.info(f"WebSocket connected for {symbol} (total: {len(active_connections[symbol])})")

    try:
        data_agent = get_data_agent()
        last_candle_time = None

        while True:
            try:
                # Fetch the latest candle data
                end_date = datetime.now()
                start_date = end_date - timedelta(minutes=30)  # Last 30 min

                df = data_agent.fetch_historical_sync(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe="5m",
                )

                if df is not None and len(df) > 0:
                    # Get the latest row
                    last_row = df.iloc[-1]
                    ts = last_row.get("bar_ts", last_row.get("timestamp", df.index[-1]))
                    if hasattr(ts, "isoformat"):
                        ts_str = ts.isoformat()
                    else:
                        ts_str = str(ts)

                    candle = {
                        "type": "candle",
                        "symbol": symbol,
                        "timestamp": ts_str,
                        "open": float(last_row.get("open", 0)),
                        "high": float(last_row.get("high", 0)),
                        "low": float(last_row.get("low", 0)),
                        "close": float(last_row.get("close", 0)),
                        "volume": int(last_row.get("volume", 0)),
                    }

                    # Only send if candle changed
                    candle_key = f"{ts_str}_{candle['close']}"
                    if candle_key != last_candle_time:
                        last_candle_time = candle_key
                        await websocket.send_json(candle)

                    # Also send current price tick
                    await websocket.send_json({
                        "type": "tick",
                        "symbol": symbol,
                        "price": candle["close"],
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "volume": candle["volume"],
                    })

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })

            # Wait 5 seconds before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
    finally:
        active_connections.get(symbol, set()).discard(websocket)
        if symbol in active_connections and not active_connections[symbol]:
            del active_connections[symbol]
