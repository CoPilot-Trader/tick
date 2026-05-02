"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  AreaSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type AreaData,
  type UTCTimestamp,
  CrosshairMode,
  LineStyle,
} from "lightweight-charts";
import type { Candle } from "@/lib/api";

type Props = {
  symbol: string;
  initialCandles: Candle[];
  height?: number;
  variant?: "hero" | "showcase";
};

function toCandle(c: Candle): CandlestickData<UTCTimestamp> {
  return {
    time: Math.floor(new Date(c.timestamp).getTime() / 1000) as UTCTimestamp,
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
  };
}

function toArea(c: Candle): AreaData<UTCTimestamp> {
  return {
    time: Math.floor(new Date(c.timestamp).getTime() / 1000) as UTCTimestamp,
    value: c.close,
  };
}

// Simple synthetic forward projection so the chart shows a "predicted path"
// extending past the last candle. This is purely visual on the marketing
// page — the real prediction surface lives in the dashboard. Uses a
// momentum + mean-reversion blend seeded from the last 20 closes.
function projectForward(candles: Candle[], steps = 16): AreaData<UTCTimestamp>[] {
  if (candles.length < 4) return [];
  const last = candles[candles.length - 1];
  const lastTs = Math.floor(new Date(last.timestamp).getTime() / 1000);
  const recent = candles.slice(-20);
  const closes = recent.map((c) => c.close);
  const mean = closes.reduce((a, b) => a + b, 0) / closes.length;
  // Average step in seconds between bars (default to 5 min)
  const dt =
    candles.length > 1
      ? Math.max(
          60,
          Math.floor(
            (new Date(last.timestamp).getTime() -
              new Date(candles[candles.length - 2].timestamp).getTime()) /
              1000,
          ),
        )
      : 300;
  // Recent momentum
  const mom =
    (closes[closes.length - 1] - closes[0]) / Math.max(1, closes.length - 1);

  const out: AreaData<UTCTimestamp>[] = [
    { time: lastTs as UTCTimestamp, value: last.close },
  ];
  let v = last.close;
  for (let i = 1; i <= steps; i++) {
    const reversion = (mean - v) * 0.06;
    const drift = mom * 0.6;
    v = v + drift + reversion;
    out.push({ time: (lastTs + i * dt) as UTCTimestamp, value: v });
  }
  return out;
}

export function LiveChart({
  symbol,
  initialCandles,
  height,
  variant = "hero",
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const predSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const [candles, setCandles] = useState<Candle[]>(initialCandles);

  // Build chart once
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: height ?? el.clientHeight,
      layout: {
        background: { color: "transparent" },
        textColor: "#6b7689",
        fontFamily:
          "JetBrains Mono, ui-monospace, SF Mono, Consolas, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(244, 246, 250, 0.04)" },
        horzLines: { color: "rgba(244, 246, 250, 0.04)" },
      },
      rightPriceScale: {
        borderColor: "rgba(244, 246, 250, 0.06)",
        scaleMargins: { top: 0.12, bottom: 0.06 },
      },
      timeScale: {
        borderColor: "rgba(244, 246, 250, 0.06)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "rgba(0, 230, 196, 0.5)",
          width: 1,
          style: LineStyle.Dashed,
        },
        horzLine: {
          color: "rgba(0, 230, 196, 0.5)",
          width: 1,
          style: LineStyle.Dashed,
        },
      },
      handleScroll: variant === "hero" ? false : true,
      handleScale: variant === "hero" ? false : true,
    });

    const candle = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const pred = chart.addSeries(AreaSeries, {
      lineColor: "#00e6c4",
      topColor: "rgba(0, 230, 196, 0.28)",
      bottomColor: "rgba(0, 230, 196, 0.0)",
      lineWidth: 2,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;
    candleSeriesRef.current = candle;
    predSeriesRef.current = pred;

    // Initial paint
    candle.setData(initialCandles.map(toCandle));
    pred.setData(projectForward(initialCandles));
    chart.timeScale().fitContent();

    // Resize handling
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        const h = entry.contentRect.height;
        chart.applyOptions({ width: w, height: h });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      predSeriesRef.current = null;
    };
    // Only build the chart once — subsequent updates flow through setData below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Refresh data every 30s and after symbol change
  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const res = await fetch(
          `/api/ohlcv?symbol=${symbol}&timeframe=5m&days=1`,
          { cache: "no-store" },
        );
        if (!res.ok) return;
        const json = (await res.json()) as { candles: Candle[] };
        if (cancelled) return;
        if (Array.isArray(json.candles) && json.candles.length > 0) {
          setCandles(json.candles);
        }
      } catch {
        // keep last good
      }
    };
    const id = setInterval(tick, 30_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [symbol]);

  // Push new data into the series whenever it changes
  useEffect(() => {
    const c = candleSeriesRef.current;
    const p = predSeriesRef.current;
    if (!c || !p) return;
    c.setData(candles.map(toCandle));
    p.setData(projectForward(candles));
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: height ? `${height}px` : "100%" }}
    />
  );
}
