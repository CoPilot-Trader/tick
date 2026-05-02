import { NextRequest, NextResponse } from "next/server";
import { fetchOhlcv } from "@/lib/api";

// Server-side proxy for OHLCV. The hero / showcase chart polls this so the
// browser never needs to know the backend URL or worry about CORS.

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const symbol = (searchParams.get("symbol") ?? "AAPL").toUpperCase();
  const timeframe = (searchParams.get("timeframe") ?? "5m") as
    | "5m"
    | "1h"
    | "1d";
  const days = Math.max(
    1,
    Math.min(60, parseInt(searchParams.get("days") ?? "1", 10) || 1),
  );

  try {
    const candles = await fetchOhlcv(symbol, timeframe, days);
    return NextResponse.json({ symbol, timeframe, days, candles });
  } catch (e) {
    return NextResponse.json(
      { symbol, timeframe, days, candles: [], error: String(e) },
      { status: 200 },
    );
  }
}
