'use client';

import { useEffect, useRef, useMemo, useCallback, forwardRef, useImperativeHandle } from 'react';
import {
  createChart,
  createSeriesMarkers,
  createTextWatermark,
  CandlestickSeries,
  LineSeries,
  AreaSeries,
  HistogramSeries,
  IChartApi,
  CandlestickData,
  LineData,
  HistogramData,
  ColorType,
  CrosshairMode,
  Time,
  LineStyle,
} from 'lightweight-charts';
import { StockData, PredictionPoint, GraphFilters, PredictionHistoryEntry } from '@/types';
import { formatEasternAxis } from '@/lib/time';

// ── Technical indicator helpers ─────────────────────────────────────────

function sma(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += values[j];
      result.push(sum / period);
    }
  }
  return result;
}

function ema(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  const k = 2 / (period + 1);
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else if (i === period - 1) {
      let sum = 0;
      for (let j = 0; j < period; j++) sum += values[j];
      result.push(sum / period);
    } else {
      const prev = result[i - 1]!;
      result.push(values[i] * k + prev * (1 - k));
    }
  }
  return result;
}

function computeRSI(closes: number[], period = 14): (number | null)[] {
  const result: (number | null)[] = [];
  if (closes.length < period + 1) return closes.map(() => null);

  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i++) {
    const change = closes[i] - closes[i - 1];
    if (change > 0) avgGain += change;
    else avgLoss += Math.abs(change);
  }
  avgGain /= period;
  avgLoss /= period;

  for (let i = 0; i < period; i++) result.push(null);
  const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
  result.push(100 - 100 / (1 + rs));

  for (let i = period + 1; i < closes.length; i++) {
    const change = closes[i] - closes[i - 1];
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    const rsi = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    result.push(rsi);
  }
  return result;
}

function computeMACD(closes: number[]): {
  macd: (number | null)[];
  signal: (number | null)[];
  histogram: (number | null)[];
} {
  const ema12 = ema(closes, 12);
  const ema26 = ema(closes, 26);
  const macdLine: (number | null)[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (ema12[i] !== null && ema26[i] !== null) {
      macdLine.push(ema12[i]! - ema26[i]!);
    } else {
      macdLine.push(null);
    }
  }
  const nonNull = macdLine.filter((v) => v !== null) as number[];
  const signalRaw = ema(nonNull, 9);
  const signal: (number | null)[] = [];
  let si = 0;
  for (let i = 0; i < macdLine.length; i++) {
    if (macdLine[i] !== null) {
      signal.push(signalRaw[si] ?? null);
      si++;
    } else {
      signal.push(null);
    }
  }
  const histogram: (number | null)[] = macdLine.map((v, i) =>
    v !== null && signal[i] !== null ? v - signal[i]! : null
  );
  return { macd: macdLine, signal, histogram };
}

function computeBollingerBands(
  closes: number[],
  period = 20,
  stdDev = 2
): { upper: (number | null)[]; lower: (number | null)[] } {
  const middle = sma(closes, period);
  const upper: (number | null)[] = [];
  const lower: (number | null)[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (middle[i] === null) {
      upper.push(null);
      lower.push(null);
    } else {
      let variance = 0;
      for (let j = i - period + 1; j <= i; j++) {
        variance += (closes[j] - middle[i]!) ** 2;
      }
      const std = Math.sqrt(variance / period);
      upper.push(middle[i]! + stdDev * std);
      lower.push(middle[i]! - stdDev * std);
    }
  }
  return { upper, lower };
}

/**
 * Fit (or pan to) the time + price range that covers the signal lines, so the
 * user actually sees the level / entry / stop / target horizontal lines on the
 * candle chart. Without this, the time-only fit can land on a window where the
 * signal prices fall outside the visible price scale.
 *
 * If `singleSignalTimeISO` is given, we pan to that single signal (narrow time
 * window) but still include the matching signal's prices in the price scale.
 */
function fitOrPanSignals(
  chart: any,
  candleSeries: any,
  signals: any[] | undefined,
  singleSignalTimeISO?: string,
): void {
  if (!chart || !signals || signals.length === 0) return;

  // Pick the relevant subset of signals — either all of them (fit), or the
  // one whose timestamp matches the requested pan target.
  let subset = signals;
  if (singleSignalTimeISO) {
    const target = new Date(singleSignalTimeISO).getTime();
    subset = signals.filter(s => Math.abs(new Date(s.signal_time).getTime() - target) < 60_000);
    if (subset.length === 0) subset = signals; // safety fallback
  }

  // Time range: ±2 days padding for "fit all", ±6h for "pan to one"
  const times = subset.map(s => Math.floor(new Date(s.signal_time).getTime() / 1000));
  const timePadding = singleSignalTimeISO ? 3600 * 6 : 86400 * 2;
  const fromT = Math.min(...times) - timePadding;
  const toT = Math.max(...times) + timePadding;

  try {
    chart.timeScale().setVisibleRange({ from: fromT as any, to: toT as any });
  } catch { /* noop */ }

  // Price range: include every level / entry / stop / T1 / T2 price across the
  // subset, then pad by 2% so the lines don't sit on the chart edge.
  if (!candleSeries) return;
  const prices: number[] = [];
  for (const s of subset) {
    if (typeof s.level_price === 'number') prices.push(s.level_price);
    if (typeof s.entry_price === 'number') prices.push(s.entry_price);
    if (typeof s.stop_price === 'number') prices.push(s.stop_price);
    if (typeof s.target1_price === 'number') prices.push(s.target1_price);
    if (typeof s.target2_price === 'number') prices.push(s.target2_price);
  }
  if (prices.length === 0) return;

  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const pad = Math.max((maxP - minP) * 0.05, maxP * 0.02);

  try {
    // Switch the candle price scale out of autoScale so our manual range sticks.
    candleSeries.priceScale().applyOptions({ autoScale: false });
    candleSeries.applyOptions({
      autoscaleInfoProvider: () => ({
        priceRange: { minValue: minP - pad, maxValue: maxP + pad },
      }),
    });
  } catch { /* noop */ }
}

function formatVolume(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return '—';
  if (v >= 1_000_000_000) return (v / 1_000_000_000).toFixed(2) + 'B';
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(2) + 'M';
  if (v >= 1_000) return (v / 1_000).toFixed(2) + 'K';
  return v.toFixed(0);
}

/** Format a duration in seconds as a compact "2d 3h", "5h 10m", "45m" string. */
function formatTimeSpan(seconds: number): string {
  if (!seconds || seconds < 0) return '0m';
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function toTime(ts: string): Time {
  return Math.floor(new Date(ts).getTime() / 1000) as Time;
}

// ─────────────────────────────────────────────────────────────────────────

export interface CandlestickChartHandle {
  takeScreenshot: () => void;
  resetView: () => void;
  fitToSignals: () => void;
  panToSignal: (signalTimeISO: string) => void;
}

interface CandlestickChartProps {
  data: StockData;
  selectedPrediction: PredictionPoint | null;
  onPredictionClick: (prediction: PredictionPoint | null) => void;
  filters: GraphFilters;
  onFilterChange: (filters: GraphFilters) => void;
  fusionSignal?: { signal: string; confidence: number } | null;
  activeTool?: string;
  onSignalsLogOpen?: () => void;
  barSize?: string;
}

const CandlestickChart = forwardRef<CandlestickChartHandle, CandlestickChartProps>(function CandlestickChart({
  data,
  selectedPrediction,
  onPredictionClick,
  filters,
  onFilterChange,
  fusionSignal,
  activeTool = 'crosshair',
  onSignalsLogOpen,
  barSize,
}, ref) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const rsiContainerRef = useRef<HTMLDivElement>(null);
  const macdContainerRef = useRef<HTMLDivElement>(null);
  const predAccContainerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const rsiChartRef = useRef<IChartApi | null>(null);
  const macdChartRef = useRef<IChartApi | null>(null);
  const predAccChartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const livePriceRef = useRef<HTMLSpanElement>(null);
  // Measure / ruler tool overlays (TradingView-style click-drag measurement)
  const measureBoxRef = useRef<HTMLDivElement>(null);
  const measurePopupRef = useRef<HTMLDivElement>(null);
  // Preserve the user's zoom / pan across chart rebuilds (timeframe change, signals toggle, etc.)
  const preservedRangeRef = useRef<{ from: number; to: number } | null>(null);
  const lastSymbolRef = useRef<string>(data.symbol);
  useEffect(() => {
    if (lastSymbolRef.current !== data.symbol) {
      // Different ticker — discard the preserved range so we fitContent fresh
      preservedRangeRef.current = null;
      lastSymbolRef.current = data.symbol;
    }
  }, [data.symbol]);
  // OHLC HUD refs — updated live by the WebSocket candle handler
  const hudOpenRef = useRef<HTMLSpanElement>(null);
  const hudHighRef = useRef<HTMLSpanElement>(null);
  const hudLowRef = useRef<HTMLSpanElement>(null);
  const hudCloseRef = useRef<HTMLSpanElement>(null);
  const hudVolRef = useRef<HTMLSpanElement>(null);
  const hudCloseColorRef = useRef<HTMLSpanElement>(null);

  // Expose screenshot & reset to parent
  useImperativeHandle(ref, () => ({
    takeScreenshot() {
      if (!chartContainerRef.current) return;
      const canvas = chartContainerRef.current.querySelector('canvas');
      if (!canvas) return;
      const link = document.createElement('a');
      link.download = `${data.symbol}-chart-${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    },
    resetView() {
      chartRef.current?.timeScale().fitContent();
    },
    fitToSignals() {
      fitOrPanSignals(chartRef.current, candleSeriesRef.current, data.level_rejection_signals);
    },
    panToSignal(signalTimeISO: string) {
      fitOrPanSignals(chartRef.current, candleSeriesRef.current, data.level_rejection_signals, signalTimeISO);
    },
  }), [data.symbol, data.level_rejection_signals]);

  // Helper used by the in-chart "X signals ↔ fit" badge
  const fitChartToSignals = useCallback(() => {
    fitOrPanSignals(chartRef.current, candleSeriesRef.current, data.level_rejection_signals);
  }, [data.level_rejection_signals]);

  // Pre-compute all data
  const chartData = useMemo(() => {
    const historical = data.historical_data || [];
    const closes = historical.map((p) => p.close);

    const candles: CandlestickData[] = historical.map((p) => ({
      time: toTime(p.timestamp),
      open: p.open,
      high: p.high,
      low: p.low,
      close: p.close,
    }));

    const volume: HistogramData[] = historical.map((p) => ({
      time: toTime(p.timestamp),
      value: p.volume,
      color: p.close >= p.open ? 'rgba(38, 166, 154, 0.35)' : 'rgba(239, 83, 80, 0.35)',
    }));

    const sma50vals = sma(closes, Math.min(50, Math.floor(closes.length / 2)));
    const sma200vals = sma(closes, Math.min(200, closes.length));
    const ema9vals = ema(closes, Math.min(9, Math.max(2, Math.floor(closes.length / 2))));
    const ema21vals = ema(closes, Math.min(21, Math.max(2, Math.floor(closes.length / 2))));
    const ema50vals = ema(closes, Math.min(50, Math.max(2, Math.floor(closes.length / 2))));
    const rsiVals = computeRSI(closes, Math.min(14, closes.length - 1));
    const macdVals = computeMACD(closes);
    const bb = computeBollingerBands(closes, Math.min(20, Math.floor(closes.length / 2)));

    // VWAP — Volume-Weighted Average Price. Resets per session for intraday.
    const vwapData: LineData[] = [];
    {
      let cumPV = 0;
      let cumV = 0;
      let lastSessionDate = '';
      for (let i = 0; i < historical.length; i++) {
        const p = historical[i];
        const sessionDate = (p.timestamp || '').slice(0, 10);
        // Reset accumulator when the session date changes (intraday only)
        if (sessionDate !== lastSessionDate && /^\d{4}-\d{2}-\d{2}T/.test(p.timestamp || '')) {
          cumPV = 0;
          cumV = 0;
          lastSessionDate = sessionDate;
        }
        const typical = (p.high + p.low + p.close) / 3;
        const vol = p.volume || 0;
        cumPV += typical * vol;
        cumV += vol;
        vwapData.push({ time: toTime(p.timestamp), value: cumV > 0 ? cumPV / cumV : typical });
      }
    }

    const sma50Data: LineData[] = [];
    const sma200Data: LineData[] = [];
    const ema9Data: LineData[] = [];
    const ema21Data: LineData[] = [];
    const ema50Data: LineData[] = [];
    const bbUpperData: LineData[] = [];
    const bbLowerData: LineData[] = [];
    const rsiData: LineData[] = [];
    const macdData: LineData[] = [];
    const macdSignalData: LineData[] = [];
    const macdHistData: HistogramData[] = [];

    historical.forEach((p, i) => {
      const t = toTime(p.timestamp);
      if (sma50vals[i] !== null) sma50Data.push({ time: t, value: sma50vals[i]! });
      if (sma200vals[i] !== null) sma200Data.push({ time: t, value: sma200vals[i]! });
      if (ema9vals[i] !== null) ema9Data.push({ time: t, value: ema9vals[i]! });
      if (ema21vals[i] !== null) ema21Data.push({ time: t, value: ema21vals[i]! });
      if (ema50vals[i] !== null) ema50Data.push({ time: t, value: ema50vals[i]! });
      if (bb.upper[i] !== null) bbUpperData.push({ time: t, value: bb.upper[i]! });
      if (bb.lower[i] !== null) bbLowerData.push({ time: t, value: bb.lower[i]! });
      if (rsiVals[i] !== null) rsiData.push({ time: t, value: rsiVals[i]! });
      if (macdVals.macd[i] !== null) macdData.push({ time: t, value: macdVals.macd[i]! });
      if (macdVals.signal[i] !== null) macdSignalData.push({ time: t, value: macdVals.signal[i]! });
      if (macdVals.histogram[i] !== null) {
        const v = macdVals.histogram[i]!;
        macdHistData.push({
          time: t,
          value: v,
          color: v >= 0 ? 'rgba(38, 166, 154, 0.6)' : 'rgba(239, 83, 80, 0.6)',
        });
      }
    });

    // Prediction line
    const predictionData: LineData[] = [];
    const lastCandle = historical[historical.length - 1];
    if (lastCandle) {
      predictionData.push({ time: toTime(lastCandle.timestamp), value: lastCandle.close });
    }
    (data.predictions || []).forEach((pred) => {
      predictionData.push({ time: toTime(pred.timestamp), value: pred.predicted_price });
    });

    const upperBoundData: LineData[] = [];
    const lowerBoundData: LineData[] = [];
    if (lastCandle) {
      upperBoundData.push({ time: toTime(lastCandle.timestamp), value: lastCandle.close });
      lowerBoundData.push({ time: toTime(lastCandle.timestamp), value: lastCandle.close });
    }
    (data.predictions || []).forEach((pred) => {
      upperBoundData.push({ time: toTime(pred.timestamp), value: pred.upper_bound });
      lowerBoundData.push({ time: toTime(pred.timestamp), value: pred.lower_bound });
    });

    // Signal markers
    const markers: any[] = [];
    (data.predictions || []).forEach((pred) => {
      if (pred.fused_signal) {
        markers.push({
          time: toTime(pred.timestamp),
          position: pred.fused_signal === 'BUY' ? 'belowBar' : 'aboveBar',
          color: pred.fused_signal === 'BUY' ? '#26a69a' : pred.fused_signal === 'SELL' ? '#ef5350' : '#ffb74d',
          shape: pred.fused_signal === 'BUY' ? 'arrowUp' : pred.fused_signal === 'SELL' ? 'arrowDown' : 'circle',
          text: pred.fused_signal,
        });
      }
    });

    // News event markers
    const newsMarkers: any[] = [];
    (data.news_events || []).forEach((evt) => {
      const evtTime = toTime(evt.timestamp);
      const evtNum = evtTime as number;
      // Only add if within chart's time range
      if (candles.length > 0) {
        const first = candles[0].time as number;
        const last = candles[candles.length - 1].time as number;
        if (evtNum >= first && evtNum <= last) {
          newsMarkers.push({
            time: evtTime,
            position: 'aboveBar' as const,
            color: evt.sentiment > 0 ? '#26a69a' : evt.sentiment < 0 ? '#ef5350' : '#ffb74d',
            shape: 'circle' as const,
            text: 'N',
          });
        }
      }
    });

    // Backtracking: predicted vs actual price overlay from history
    // Aggregate resolved predictions per candle (keep last prediction per candle time)
    const backtrackPredicted: LineData[] = [];
    const backtrackActual: LineData[] = [];

    if ((data.prediction_history || []).length > 0) {
      const candleTimes = candles.map(c => c.time as number);
      const hasCandleTimes = candleTimes.length > 0;

      // Map: unix time -> { predicted, actual } (last write wins)
      const timeMap = new Map<number, { predicted: number; actual: number }>();

      (data.prediction_history || []).forEach((entry: PredictionHistoryEntry) => {
        // Include entries with actual prices (resolved) or show predicted-only
        const hasActual = entry.actual_price !== null && entry.actual_price !== undefined;
        if (!hasActual && !entry.predicted_price) return;

        const targetStr = entry.target_timestamp || (entry.target_date + 'T16:00:00Z');
        const targetTs = Math.floor(new Date(targetStr).getTime() / 1000);
        if (isNaN(targetTs)) return;

        if (hasCandleTimes) {
          // Try to snap to nearest candle
          let bestCandle = candleTimes[0];
          let bestDiff = Math.abs(candleTimes[0] - targetTs);
          for (let i = 1; i < candleTimes.length; i++) {
            const diff = Math.abs(candleTimes[i] - targetTs);
            if (diff < bestDiff) {
              bestDiff = diff;
              bestCandle = candleTimes[i];
            }
          }

          if (bestDiff < 7200) {
            timeMap.set(bestCandle, {
              predicted: entry.predicted_price,
              actual: hasActual ? entry.actual_price! : entry.predicted_price,
            });
            return;
          }
        }

        // No candle match — use the prediction's own timestamp (standalone mode)
        timeMap.set(targetTs, {
          predicted: entry.predicted_price,
          actual: hasActual ? entry.actual_price! : entry.predicted_price,
        });
      });

      // Convert map to sorted arrays
      const sortedKeys = Array.from(timeMap.keys()).sort((a, b) => a - b);
      for (const t of sortedKeys) {
        const v = timeMap.get(t)!;
        backtrackPredicted.push({ time: t as unknown as Time, value: v.predicted });
        backtrackActual.push({ time: t as unknown as Time, value: v.actual });
      }
    }

    return {
      candles, volume, sma50Data, sma200Data, ema9Data, ema21Data, ema50Data, bbUpperData, bbLowerData,
      rsiData, macdData, macdSignalData, macdHistData,
      predictionData, upperBoundData, lowerBoundData, markers, newsMarkers,
      backtrackPredicted, backtrackActual,
      vwapData,
      currentPrice: closes[closes.length - 1] || 0,
    };
  }, [
    // Only depend on the arrays that actually drive what the chart renders.
    // Scalar fields (current_price, price_change, price_change_percent) are
    // intentionally excluded — they tick from the watchlist polling every 5s
    // and we don't want to rebuild the chart (and reset zoom) on every tick.
    data.symbol,
    data.historical_data,
    data.support_levels,
    data.resistance_levels,
    data.predictions,
    data.prediction_history,
    data.news_events,
    data.level_rejection_signals,
  ]);

  // ─── Build charts ────────────────────────────────────────────────────
  useEffect(() => {
    if (!chartContainerRef.current || !wrapperRef.current) return;

    // Cleanup
    try { if (chartRef.current) { chartRef.current.remove(); } } catch { /* noop */ }
    chartRef.current = null;
    try { if (rsiChartRef.current) { rsiChartRef.current.remove(); } } catch { /* noop */ }
    rsiChartRef.current = null;
    try { if (macdChartRef.current) { macdChartRef.current.remove(); } } catch { /* noop */ }
    macdChartRef.current = null;
    try { if (predAccChartRef.current) { predAccChartRef.current.remove(); } } catch { /* noop */ }
    predAccChartRef.current = null;

    const containerWidth = chartContainerRef.current.clientWidth;
    const wrapperHeight = wrapperRef.current.clientHeight;

    // Calculate dynamic heights
    const toolbarHeight = 36; // toolbar above chart
    const subChartCount = (filters.showRSI ? 1 : 0) + (filters.showMACD ? 1 : 0);
    const subChartHeight = 120;
    const subChartLabelHeight = 20;
    const availableHeight = wrapperHeight - toolbarHeight;
    const mainChartHeight = Math.max(200, availableHeight - subChartCount * (subChartHeight + subChartLabelHeight));

    // Strip the TradingView attribution logo that lightweight-charts injects
    const stripAttribution = (container: HTMLElement) => {
      // Remove the <a id="tv-attr-logo"> and its companion <style> element
      const logo = container.querySelector('#tv-attr-logo');
      if (logo) {
        const prev = logo.previousElementSibling;
        if (prev && prev.tagName === 'STYLE') prev.remove();
        logo.remove();
      }
      // Also remove by href as a fallback
      container.querySelectorAll('a[href*="tradingview"]').forEach(el => el.remove());
      // Remove by the known SVG path signature
      container.querySelectorAll('svg').forEach(svg => {
        if (svg.innerHTML.includes('M14 2H2v6h6v9h6V2Z')) svg.closest('a')?.remove() || svg.remove();
      });
    };

    // Re-run periodically for the first second (library may inject after render)
    const stripAll = () => {
      if (chartContainerRef.current) stripAttribution(chartContainerRef.current);
      if (rsiContainerRef.current) stripAttribution(rsiContainerRef.current);
      if (macdContainerRef.current) stripAttribution(macdContainerRef.current);
      if (predAccContainerRef.current) stripAttribution(predAccContainerRef.current);
      // Walk up to wrapper to catch any that escaped
      if (wrapperRef.current) stripAttribution(wrapperRef.current);
    };
    const stripTimers = [
      setTimeout(stripAll, 50),
      setTimeout(stripAll, 200),
      setTimeout(stripAll, 500),
      setTimeout(stripAll, 1000),
    ];

    // ─── Professional chart colors ────────────────────────────────────
    const bgColor = '#131722';
    const gridColor = '#1e222d';
    const textColor = '#787b86';
    const borderColor = '#2a2e39';

    // ─── Main chart ──────────────────────────────────────────────────
    const chart = createChart(chartContainerRef.current, {
      width: containerWidth,
      height: mainChartHeight,
      layout: {
        background: { type: ColorType.Solid, color: bgColor },
        textColor: textColor,
        fontSize: 11,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      },
      // All axis + crosshair times rendered in US Eastern (market timezone)
      localization: {
        timeFormatter: (t: number) => formatEasternAxis(t, true),
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      crosshair: {
        mode: activeTool === 'crosshair' ? CrosshairMode.Normal : CrosshairMode.Magnet,
        vertLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
        horzLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
      },
      rightPriceScale: {
        borderColor: borderColor,
        scaleMargins: { top: 0.05, bottom: 0.15 },
      },
      timeScale: {
        borderColor: borderColor,
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
        barSpacing: 8,
        tickMarkFormatter: (t: number, tickMarkType: number) => formatEasternAxis(t, true, tickMarkType),
      },
    } as any);
    chartRef.current = chart;

    // Candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candleSeries.setData(chartData.candles);
    candleSeriesRef.current = candleSeries;

    // Background ticker watermark — faint large ticker symbol behind the
    // candles so the user knows which symbol they're viewing without looking
    // at the small header badge. Per Tory's TradingView reference.
    try {
      const panes = chart.panes();
      if (panes && panes.length > 0) {
        // Tory's TradingView reference: ticker + interval on the top line,
        // description (company / fund name) below. Comma separator, not bullet.
        // Opacity bumped from 4.5% → 9% so the watermark actually reads at
        // a glance without competing with the candles.
        const tickerLine = barSize ? `${data.symbol}, ${barSize}` : data.symbol;
        const descLine = data.name && data.name !== data.symbol ? data.name : '';
        const lines: { text: string; color: string; fontSize: number; fontStyle?: string }[] = [
          { text: tickerLine, color: 'rgba(255, 255, 255, 0.09)', fontSize: 120, fontStyle: 'bold' },
        ];
        if (descLine) {
          lines.push({ text: descLine, color: 'rgba(255, 255, 255, 0.06)', fontSize: 28 });
        }
        createTextWatermark(panes[0], { horzAlign: 'center', vertAlign: 'center', lines });
      }
    } catch { /* watermark is decorative — never block the chart */ }

    // Current price line
    if (chartData.currentPrice > 0) {
      const lastCandle = chartData.candles[chartData.candles.length - 1];
      const isUp = lastCandle ? lastCandle.close >= lastCandle.open : true;
      try {
        candleSeries.createPriceLine({
          price: chartData.currentPrice,
          color: isUp ? '#26a69a' : '#ef5350',
          lineWidth: 1,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: '',
        });
      } catch { /* noop */ }
    }

    // Volume (always on)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    volumeSeries.setData(chartData.volume);
    volumeSeriesRef.current = volumeSeries;
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    // ─── Overlays ────────────────────────────────────────────────────

    // VWAP — Volume-Weighted Average Price (live, computed from OHLCV)
    if (filters.showVWAP && chartData.vwapData.length > 0) {
      const v = chart.addSeries(LineSeries, {
        color: '#ab47bc',
        lineWidth: 2,
        title: 'VWAP',
        priceLineVisible: false,
      });
      v.setData(chartData.vwapData);
    }

    // SMA lines
    if (filters.showMovingAverages) {
      if (chartData.sma50Data.length > 0) {
        const s = chart.addSeries(LineSeries, { color: '#f7a21b', lineWidth: 1, title: 'MA 50' });
        s.setData(chartData.sma50Data);
      }
      if (chartData.sma200Data.length > 0) {
        const s = chart.addSeries(LineSeries, { color: '#e91e63', lineWidth: 1, title: 'MA 200' });
        s.setData(chartData.sma200Data);
      }
    }
    // EMA lines — each toggled independently so user can show one, two, or all three.
    if (filters.showEMA9 && chartData.ema9Data.length > 0) {
      const s = chart.addSeries(LineSeries, { color: '#42a5f5', lineWidth: 1, title: 'EMA 9' });
      s.setData(chartData.ema9Data);
    }
    if (filters.showEMA21 && chartData.ema21Data.length > 0) {
      const s = chart.addSeries(LineSeries, { color: '#ffca28', lineWidth: 1, title: 'EMA 21' });
      s.setData(chartData.ema21Data);
    }
    if (filters.showEMA50 && chartData.ema50Data.length > 0) {
      const s = chart.addSeries(LineSeries, { color: '#ab47bc', lineWidth: 1, title: 'EMA 50' });
      s.setData(chartData.ema50Data);
    }

    // Bollinger Bands
    if (filters.showBollingerBands) {
      if (chartData.bbUpperData.length > 0) {
        const s = chart.addSeries(LineSeries, { color: '#7b1fa2', lineWidth: 1, lineStyle: LineStyle.Dashed, title: 'BB' });
        s.setData(chartData.bbUpperData);
      }
      if (chartData.bbLowerData.length > 0) {
        const s = chart.addSeries(LineSeries, { color: '#7b1fa2', lineWidth: 1, lineStyle: LineStyle.Dashed, title: '' });
        s.setData(chartData.bbLowerData);
      }
    }

    // Support/Resistance
    if (filters.showSupportResistance) {
      (data.support_levels || []).forEach((level) => {
        try {
          candleSeries.createPriceLine({
            price: level.price, color: '#26a69a', lineWidth: 1,
            lineStyle: LineStyle.Dashed, axisLabelVisible: true,
            title: `Support ${level.price.toFixed(2)}`,
          });
        } catch { /* noop */ }
      });
      (data.resistance_levels || []).forEach((level) => {
        try {
          candleSeries.createPriceLine({
            price: level.price, color: '#ef5350', lineWidth: 1,
            lineStyle: LineStyle.Dashed, axisLabelVisible: true,
            title: `Resistance ${level.price.toFixed(2)}`,
          });
        } catch { /* noop */ }
      });
      // Psychological round-number levels — dotted orange, lower-contrast.
      // These are derived ($5/$10 increments near current price), not detected.
      (data.psychological_levels || []).forEach((level) => {
        try {
          candleSeries.createPriceLine({
            price: level.price,
            color: 'rgba(255, 167, 38, 0.55)',
            lineWidth: 1,
            lineStyle: LineStyle.Dotted,
            axisLabelVisible: true,
            title: `$${level.price.toFixed(2)}`,
          });
        } catch { /* noop */ }
      });
    }

    // Level Rejection signals (external — from Tory's pipeline)
    // Density strategy (Tory: "chart feels too busy with lines"):
    //   1) Only render signals whose timestamp falls inside the chart's
    //      currently visible time range.
    //   2) Deduplicate signals whose prices land within 0.1% of each other —
    //      one line at the cluster average, with a count badge in the title.
    //   3) Re-render dynamically on pan/zoom so the user always sees just
    //      the signals relevant to the window they're looking at.
    if (filters.showLevelRejection && data.level_rejection_signals && data.level_rejection_signals.length > 0) {
      const allSignals = data.level_rejection_signals;
      let renderedLines: any[] = [];

      // All markers always shown (lightweight overlays at signal time), but
      // the heavy price lines are filtered to visible-range.
      const allMarkers = allSignals.map(s => ({
        time: Math.floor(new Date(s.signal_time).getTime() / 1000),
        position: 'belowBar' as const,
        color: s.target1_hit ? '#4caf50' : '#f44336',
        shape: 'arrowUp' as const,
        text: s.target1_hit ? 'W' : 'L',
      })).sort((a, b) => a.time - b.time);
      try { (candleSeries as any).setMarkers(allMarkers); } catch { /* noop */ }

      const clearLines = () => {
        for (const line of renderedLines) {
          try { candleSeries.removePriceLine(line); } catch { /* noop */ }
        }
        renderedLines = [];
      };

      // Cluster nearby prices into one rendered line with a count.
      const clusterPrices = (entries: { price: number; label: string }[]) => {
        if (entries.length === 0) return [];
        const sorted = [...entries].sort((a, b) => a.price - b.price);
        const clusters: { price: number; count: number; label: string }[] = [];
        for (const e of sorted) {
          const last = clusters[clusters.length - 1];
          if (last && Math.abs(e.price - last.price) / last.price < 0.001) {
            last.price = (last.price * last.count + e.price) / (last.count + 1);
            last.count += 1;
          } else {
            clusters.push({ price: e.price, count: 1, label: e.label });
          }
        }
        return clusters;
      };

      const renderForVisibleRange = (fromSec: number, toSec: number) => {
        clearLines();
        const inWindow = allSignals.filter(s => {
          const t = new Date(s.signal_time).getTime() / 1000;
          return t >= fromSec && t <= toSec;
        });

        const levels: { price: number; label: string }[] = [];
        const entries: { price: number; label: string }[] = [];
        const stops: { price: number; label: string }[] = [];
        const t1s: { price: number; label: string }[] = [];
        const t2s: { price: number; label: string }[] = [];
        for (const s of inWindow) {
          levels.push({ price: s.level_price, label: s.level_type });
          entries.push({ price: s.entry_price, label: 'entry' });
          stops.push({ price: s.stop_price, label: 'stop' });
          t1s.push({ price: s.target1_price, label: 't1' });
          if (s.target2_price != null) t2s.push({ price: s.target2_price, label: 't2' });
        }

        const addLine = (price: number, color: string, style: LineStyle, title: string, axisLabel: boolean) => {
          try { renderedLines.push(candleSeries.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: axisLabel, title })); } catch { /* noop */ }
        };

        for (const c of clusterPrices(levels)) addLine(c.price, '#00bcd4', LineStyle.Solid, `SIG Level · ${c.label}${c.count > 1 ? ` ×${c.count}` : ''}`, true);
        for (const c of clusterPrices(entries)) addLine(c.price, '#ffc107', LineStyle.Dotted, `SIG Entry${c.count > 1 ? ` ×${c.count}` : ''}`, false);
        for (const c of clusterPrices(stops)) addLine(c.price, '#f44336', LineStyle.Dashed, `SIG Stop${c.count > 1 ? ` ×${c.count}` : ''}`, false);
        for (const c of clusterPrices(t1s)) addLine(c.price, '#4caf50', LineStyle.Dashed, `SIG Target 1${c.count > 1 ? ` ×${c.count}` : ''}`, false);
        for (const c of clusterPrices(t2s)) addLine(c.price, '#8bc34a', LineStyle.Dashed, `SIG Target 2${c.count > 1 ? ` ×${c.count}` : ''}`, false);
      };

      // Initial render covering the full data range (the visible-range
      // subscription will narrow it on first paint).
      const candleTimes = chartData.candles.map(c => c.time as number);
      if (candleTimes.length > 0) {
        renderForVisibleRange(candleTimes[0], candleTimes[candleTimes.length - 1]);
      }

      // Re-render on pan/zoom so the chart only ever shows lines for what's
      // actually in view.
      chart.timeScale().subscribeVisibleTimeRangeChange((range) => {
        if (!range) return;
        const from = typeof range.from === 'number' ? range.from : NaN;
        const to = typeof range.to === 'number' ? range.to : NaN;
        if (!isFinite(from) || !isFinite(to)) return;
        renderForVisibleRange(from, to);
      });
    }

    // Prediction forecast — prominent area band + bold line
    if (filters.showPredictedPrice && chartData.predictionData.length > 1) {
      // Upper confidence bound as filled area (shows the prediction zone)
      if (chartData.upperBoundData.length > 1) {
        const upperArea = chart.addSeries(AreaSeries, {
          lineColor: 'rgba(66, 165, 245, 0.3)',
          topColor: 'rgba(66, 165, 245, 0.25)',
          bottomColor: 'rgba(66, 165, 245, 0.02)',
          lineWidth: 1,
          crosshairMarkerVisible: false,
          priceLineVisible: false,
        });
        upperArea.setData(chartData.upperBoundData);
      }

      // Main forecast line — bold and visible
      const predSeries = chart.addSeries(LineSeries, {
        color: '#42a5f5', lineWidth: 3, title: 'Forecast',
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 5,
      });
      predSeries.setData(chartData.predictionData);

      // Show confidence bounds as dashed lines
      if (filters.showConfidenceBounds) {
        if (chartData.upperBoundData.length > 1) {
          const up = chart.addSeries(LineSeries, { color: '#42a5f580', lineWidth: 1, lineStyle: LineStyle.Dashed, title: '' });
          up.setData(chartData.upperBoundData);
        }
        if (chartData.lowerBoundData.length > 1) {
          const lo = chart.addSeries(LineSeries, { color: '#42a5f580', lineWidth: 1, lineStyle: LineStyle.Dashed, title: '' });
          lo.setData(chartData.lowerBoundData);
        }
      }

      // Add price label at the forecast endpoint
      const lastPred = chartData.predictionData[chartData.predictionData.length - 1];
      if (lastPred) {
        try {
          predSeries.createPriceLine({
            price: lastPred.value,
            color: '#42a5f5',
            lineWidth: 1,
            lineStyle: LineStyle.Dotted,
            axisLabelVisible: true,
            title: `▸ ${lastPred.value.toFixed(2)}`,
          });
        } catch { /* noop */ }
      }
    }

    // Signal markers + news markers combined (must be sorted by time)
    const allMarkers = [...chartData.markers];
    if (filters.showNewsEvents && chartData.newsMarkers.length > 0) {
      allMarkers.push(...chartData.newsMarkers);
    }
    if (allMarkers.length > 0) {
      allMarkers.sort((a, b) => (a.time as number) - (b.time as number));
      createSeriesMarkers(candleSeries, allMarkers);
    }

    // Restore the user's preserved zoom range if we have one. Otherwise show
    // the most recent ~80 candles at a TradingView-like comfortable density
    // (Tory: "candles too small by default" — fitContent crammed everything
    // into the viewport).
    if (preservedRangeRef.current) {
      try {
        chart.timeScale().setVisibleRange(preservedRangeRef.current as any);
      } catch { chart.timeScale().fitContent(); }
    } else {
      const total = chartData.candles.length;
      const DEFAULT_BARS = 80;
      if (total > DEFAULT_BARS) {
        try {
          chart.timeScale().setVisibleLogicalRange({
            from: total - DEFAULT_BARS,
            to: total + 5, // small right padding for forecast / live updates
          });
        } catch { chart.timeScale().fitContent(); }
      } else {
        chart.timeScale().fitContent();
      }
    }

    // Persist the visible range whenever the user pans or zooms
    chart.timeScale().subscribeVisibleTimeRangeChange((range) => {
      if (range && typeof range.from === 'number' && typeof range.to === 'number') {
        preservedRangeRef.current = { from: range.from as number, to: range.to as number };
      }
    });

    // ─── News tooltip on crosshair hover ─────────────────────────────
    if (filters.showNewsEvents && (data.news_events || []).length > 0) {
      // Build time->news lookup (within 1 hour tolerance)
      const newsLookup = new Map<number, { title: string; source: string; sentiment: number }>();
      (data.news_events || []).forEach((evt) => {
        const t = Math.floor(new Date(evt.timestamp).getTime() / 1000);
        newsLookup.set(t, { title: evt.title, source: evt.source, sentiment: evt.sentiment });
      });

      chart.subscribeCrosshairMove((param) => {
        const tooltip = tooltipRef.current;
        if (!tooltip) return;

        if (!param.time || !param.point) {
          tooltip.style.display = 'none';
          return;
        }

        const crosshairTime = param.time as number;
        // Find nearest news within 1-hour window
        let matched: { title: string; source: string; sentiment: number } | null = null;
        for (const [t, news] of newsLookup.entries()) {
          if (Math.abs(crosshairTime - t) < 3600) {
            matched = news;
            break;
          }
        }

        if (matched) {
          tooltip.style.display = 'block';
          tooltip.style.left = `${param.point.x + 15}px`;
          tooltip.style.top = `${param.point.y - 10}px`;
          tooltip.innerHTML = `
            <div style="font-weight:600;margin-bottom:2px;color:#d1d4dc">${matched.title.slice(0, 80)}${matched.title.length > 80 ? '...' : ''}</div>
            <div style="font-size:10px;color:#787b86">${matched.source}</div>
            <div style="font-size:10px;margin-top:2px;color:${matched.sentiment > 0 ? '#26a69a' : matched.sentiment < 0 ? '#ef5350' : '#787b86'}">
              Sentiment: ${matched.sentiment > 0 ? '+' : ''}${matched.sentiment.toFixed(2)}
            </div>
          `;
        } else {
          tooltip.style.display = 'none';
        }
      });
    }

    // ─── RSI sub-chart ──────────────────────────────────────────────
    if (filters.showRSI && rsiContainerRef.current) {
      const rsiChart = createChart(rsiContainerRef.current, {
        width: containerWidth,
        height: subChartHeight,
        layout: { background: { type: ColorType.Solid, color: bgColor }, textColor, fontSize: 10 },
        grid: { vertLines: { color: gridColor }, horzLines: { color: gridColor } },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
          horzLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
        },
        rightPriceScale: { borderColor },
        timeScale: { visible: false },
      });
      rsiChartRef.current = rsiChart;

      const rsiSeries = rsiChart.addSeries(LineSeries, { color: '#7e57c2', lineWidth: 1, title: 'RSI' });
      rsiSeries.setData(chartData.rsiData);
      rsiSeries.createPriceLine({ price: 70, color: '#ef535080', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: false, title: '' });
      rsiSeries.createPriceLine({ price: 30, color: '#26a69a80', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: false, title: '' });
      rsiChart.timeScale().fitContent();
      chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (range) rsiChart.timeScale().setVisibleLogicalRange(range);
      });
    }

    // ─── MACD sub-chart ─────────────────────────────────────────────
    if (filters.showMACD && macdContainerRef.current) {
      const macdChart = createChart(macdContainerRef.current, {
        width: containerWidth,
        height: subChartHeight,
        layout: { background: { type: ColorType.Solid, color: bgColor }, textColor, fontSize: 10 },
        grid: { vertLines: { color: gridColor }, horzLines: { color: gridColor } },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
          horzLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
        },
        rightPriceScale: { borderColor },
        timeScale: { visible: false },
      });
      macdChartRef.current = macdChart;

      if (chartData.macdHistData.length > 0) {
        const h = macdChart.addSeries(HistogramSeries, { title: '' });
        h.setData(chartData.macdHistData);
      }
      if (chartData.macdData.length > 0) {
        const m = macdChart.addSeries(LineSeries, { color: '#2962ff', lineWidth: 1, title: 'MACD' });
        m.setData(chartData.macdData);
      }
      if (chartData.macdSignalData.length > 0) {
        const s = macdChart.addSeries(LineSeries, { color: '#ff6d00', lineWidth: 1, title: 'Signal' });
        s.setData(chartData.macdSignalData);
      }
      macdChart.timeScale().fitContent();
      chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (range) macdChart.timeScale().setVisibleLogicalRange(range);
      });
    }

    // ─── Prediction Accuracy side panel chart ──────────────────────────
    if (filters.showPredictionAccuracy && predAccContainerRef.current && (chartData.backtrackPredicted.length > 0 || chartData.backtrackActual.length > 0)) {
      const predAccWidth = predAccContainerRef.current.clientWidth || Math.floor(containerWidth * 0.3);
      const predAccHeight = predAccContainerRef.current.clientHeight || mainChartHeight;

      const predAccChart = createChart(predAccContainerRef.current, {
        width: predAccWidth,
        height: predAccHeight,
        layout: { background: { type: ColorType.Solid, color: bgColor }, textColor, fontSize: 10 },
        localization: { timeFormatter: (t: number) => formatEasternAxis(t, true) },
        grid: { vertLines: { color: gridColor }, horzLines: { color: gridColor } },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
          horzLine: { color: '#758696', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#2a2e39' },
        },
        rightPriceScale: { borderColor, scaleMargins: { top: 0.05, bottom: 0.05 } },
        timeScale: { borderColor, timeVisible: true, secondsVisible: false, rightOffset: 2, barSpacing: 4, tickMarkFormatter: (t: number, tickMarkType: number) => formatEasternAxis(t, true, tickMarkType) },
      });
      predAccChartRef.current = predAccChart;

      if (chartData.backtrackPredicted.length > 0) {
        const ps = predAccChart.addSeries(LineSeries, {
          color: '#ff9800', lineWidth: 2, lineStyle: LineStyle.Dashed, title: 'Predicted',
          crosshairMarkerVisible: true, crosshairMarkerRadius: 3,
        });
        ps.setData(chartData.backtrackPredicted);
      }
      if (chartData.backtrackActual.length > 0) {
        const as2 = predAccChart.addSeries(AreaSeries, {
          lineColor: '#4caf50', lineWidth: 2, title: 'Actual',
          topColor: 'rgba(76, 175, 80, 0.15)', bottomColor: 'rgba(76, 175, 80, 0.02)',
          crosshairMarkerVisible: true, crosshairMarkerRadius: 3,
        });
        as2.setData(chartData.backtrackActual);
      }

      // The Pred-vs-Actual panel has its OWN time domain (prediction dates,
      // which often differ from the candle dates — especially with PCR-shock
      // signals spanning other ranges). It must stand alone with fitContent().
      // A previous bidirectional time-axis sync with the main chart created a
      // feedback loop that made the panel flicker/jump ("refresh" issue Tory
      // flagged) — removed.
      predAccChart.timeScale().fitContent();
    }

    // ─── Resize ──────────────────────────────────────────────────────
    const handleResize = () => {
      if (!chartContainerRef.current || !wrapperRef.current) return;
      const w = chartContainerRef.current.clientWidth;
      const wh = wrapperRef.current.clientHeight;
      const sc = (filters.showRSI ? 1 : 0) + (filters.showMACD ? 1 : 0);
      const mh = Math.max(200, wh - toolbarHeight - sc * (subChartHeight + subChartLabelHeight));
      chart.applyOptions({ width: w, height: mh });
      if (rsiChartRef.current) rsiChartRef.current.applyOptions({ width: w + (predAccContainerRef.current?.clientWidth || 0) });
      if (macdChartRef.current) macdChartRef.current.applyOptions({ width: w + (predAccContainerRef.current?.clientWidth || 0) });
      if (predAccChartRef.current && predAccContainerRef.current) {
        predAccChartRef.current.applyOptions({
          width: predAccContainerRef.current.clientWidth,
          height: mh,
        });
      }
    };
    window.addEventListener('resize', handleResize);

    // ResizeObserver for container changes
    const ro = new ResizeObserver(handleResize);
    ro.observe(wrapperRef.current);

    return () => {
      stripTimers.forEach(clearTimeout);
      window.removeEventListener('resize', handleResize);
      ro.disconnect();
      try { chart.remove(); } catch { /* noop */ }
      try { if (rsiChartRef.current) { rsiChartRef.current.remove(); } } catch { /* noop */ }
      rsiChartRef.current = null;
      try { if (macdChartRef.current) { macdChartRef.current.remove(); } } catch { /* noop */ }
      macdChartRef.current = null;
      try { if (predAccChartRef.current) { predAccChartRef.current.remove(); } } catch { /* noop */ }
      predAccChartRef.current = null;
    };
  }, [chartData, filters, data.support_levels, data.resistance_levels, data.psychological_levels, activeTool]);

  // ─── WebSocket live streaming ──────────────────────────────────────
  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = API_BASE.replace(/^http/, 'ws') + `/ws/stream/${data.symbol}`;

    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);

            if (msg.type === 'candle' && candleSeriesRef.current) {
              // Update or add candle
              const candleUpdate = {
                time: Math.floor(new Date(msg.timestamp).getTime() / 1000) as Time,
                open: msg.open,
                high: msg.high,
                low: msg.low,
                close: msg.close,
              };
              candleSeriesRef.current.update(candleUpdate);

              // Update volume
              if (volumeSeriesRef.current) {
                volumeSeriesRef.current.update({
                  time: candleUpdate.time,
                  value: msg.volume,
                  color: msg.close >= msg.open ? 'rgba(38, 166, 154, 0.35)' : 'rgba(239, 83, 80, 0.35)',
                });
              }

              // Update OHLC HUD strip (live tick of current candle)
              const isUp = msg.close >= msg.open;
              const candleColor = isUp ? '#26a69a' : '#ef5350';
              if (hudOpenRef.current) hudOpenRef.current.textContent = msg.open.toFixed(2);
              if (hudHighRef.current) hudHighRef.current.textContent = msg.high.toFixed(2);
              if (hudLowRef.current) hudLowRef.current.textContent = msg.low.toFixed(2);
              if (hudCloseRef.current) {
                hudCloseRef.current.textContent = msg.close.toFixed(2);
                hudCloseRef.current.style.color = candleColor;
              }
              if (hudVolRef.current) {
                hudVolRef.current.textContent = formatVolume(msg.volume);
              }
            }

            if (msg.type === 'tick' && livePriceRef.current) {
              livePriceRef.current.textContent = msg.price.toFixed(2);
              // Also tick the close in the OHLC strip
              if (hudCloseRef.current) {
                hudCloseRef.current.textContent = msg.price.toFixed(2);
              }
            }
          } catch { /* ignore parse errors */ }
        };

        ws.onclose = () => {
          // Reconnect after 3 seconds
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          ws?.close();
        };
      } catch { /* noop */ }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null; // Prevent reconnect on intentional close
        ws.close();
      }
      wsRef.current = null;
    };
  }, [data.symbol]);

  // ─── Measure / ruler tool (TradingView-style click-drag measurement) ──
  useEffect(() => {
    if (activeTool !== 'ruler') return;
    const container = chartContainerRef.current;
    const chart = chartRef.current;
    const series = candleSeriesRef.current;
    const box = measureBoxRef.current;
    const popup = measurePopupRef.current;
    if (!container || !chart || !series || !box || !popup) return;

    let startX = 0, startY = 0;
    let dragging = false;

    const candles = chartData.candles;
    const volumes = chartData.volume;

    const clear = () => {
      box.style.display = 'none';
      popup.style.display = 'none';
      dragging = false;
    };

    const onDown = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      startX = e.clientX - rect.left;
      startY = e.clientY - rect.top;
      dragging = true;
      box.style.display = 'block';
      popup.style.display = 'block';
    };

    const onMove = (e: MouseEvent) => {
      if (!dragging) return;
      const rect = container.getBoundingClientRect();
      const curX = e.clientX - rect.left;
      const curY = e.clientY - rect.top;

      // Draw the box
      const left = Math.min(startX, curX);
      const top = Math.min(startY, curY);
      box.style.left = `${left}px`;
      box.style.top = `${top}px`;
      box.style.width = `${Math.abs(curX - startX)}px`;
      box.style.height = `${Math.abs(curY - startY)}px`;

      // Convert pixels → price/time
      const startPrice = series.coordinateToPrice(startY);
      const endPrice = series.coordinateToPrice(curY);
      const startTime = chart.timeScale().coordinateToTime(startX) as number | null;
      const endTime = chart.timeScale().coordinateToTime(curX) as number | null;

      if (startPrice == null || endPrice == null) return;

      const priceDelta = endPrice - startPrice;
      const pricePct = startPrice !== 0 ? (priceDelta / startPrice) * 100 : 0;
      const up = priceDelta >= 0;

      // Bars + volume + time span within the dragged time window
      let bars = 0;
      let volSum = 0;
      let timeSpanSec = 0;
      if (startTime != null && endTime != null) {
        const lo = Math.min(startTime, endTime);
        const hi = Math.max(startTime, endTime);
        timeSpanSec = hi - lo;
        for (let i = 0; i < candles.length; i++) {
          const t = candles[i].time as number;
          if (t >= lo && t <= hi) {
            bars++;
            if (volumes[i]) volSum += (volumes[i] as any).value || 0;
          }
        }
      }

      const sign = up ? '+' : '';
      const color = up ? '#26a69a' : '#ef5350';
      popup.innerHTML =
        `<div style="color:${color};font-weight:600;margin-bottom:3px">${sign}${priceDelta.toFixed(2)} (${sign}${pricePct.toFixed(2)}%)</div>` +
        `<div style="color:#787b86">${bars} bar${bars === 1 ? '' : 's'} · ${formatTimeSpan(timeSpanSec)}</div>` +
        `<div style="color:#787b86">Vol ${formatVolume(volSum)}</div>`;

      // Position popup near the end point, clamped inside the container
      const popupW = 150, popupH = 56;
      let px = curX + 12;
      let py = curY + 12;
      if (px + popupW > rect.width) px = curX - popupW - 12;
      if (py + popupH > rect.height) py = curY - popupH - 12;
      popup.style.left = `${Math.max(0, px)}px`;
      popup.style.top = `${Math.max(0, py)}px`;
    };

    const onUp = () => { dragging = false; };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') clear(); };

    container.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    window.addEventListener('keydown', onKey);

    return () => {
      container.removeEventListener('mousedown', onDown);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('keydown', onKey);
      clear();
    };
  }, [activeTool, chartData]);

  // Toggle helper
  const toggleFilter = useCallback(
    (key: keyof GraphFilters) => {
      onFilterChange({ ...filters, [key]: !filters[key] });
    },
    [filters, onFilterChange]
  );

  const indicatorButtons: { key: keyof GraphFilters; label: string; color: string; tip: string }[] = [
    { key: 'showMovingAverages', label: 'SMA 50/200', color: '#f7a21b', tip: 'Simple Moving Averages — 50-period (gold) and 200-period (pink)' },
    { key: 'showEMA9', label: 'EMA 9', color: '#42a5f5', tip: '9-period Exponential Moving Average — reacts faster than SMA' },
    { key: 'showEMA21', label: 'EMA 21', color: '#ffca28', tip: '21-period Exponential Moving Average — common swing-trade reference' },
    { key: 'showEMA50', label: 'EMA 50', color: '#ab47bc', tip: '50-period Exponential Moving Average — medium-term trend' },
    { key: 'showVWAP', label: 'VWAP', color: '#ab47bc', tip: 'Volume-Weighted Average Price — resets each session for intraday timeframes' },
    { key: 'showBollingerBands', label: 'BB', color: '#7b1fa2', tip: 'Bollinger Bands — 20-period SMA ± 2 standard deviations' },
    { key: 'showSupportResistance', label: 'S/R', color: '#26a69a', tip: 'Support & Resistance levels — detected by DBSCAN clustering + volume profile on live data' },
    { key: 'showRSI', label: 'RSI', color: '#7e57c2', tip: 'Relative Strength Index (14) — momentum oscillator, sub-panel below' },
    { key: 'showMACD', label: 'MACD', color: '#2962ff', tip: 'Moving Average Convergence Divergence (12/26/9) — sub-panel below' },
    { key: 'showPredictedPrice', label: 'Forecast', color: '#42a5f5', tip: 'Model price forecast for the next horizon (Prophet/LSTM ensemble)' },
    { key: 'showConfidenceBounds', label: 'Forecast Bounds', color: '#42a5f5', tip: 'Upper/lower confidence interval around the forecast line' },
    { key: 'showNewsEvents', label: 'News', color: '#ffb74d', tip: 'News event markers on the chart from the sentiment pipeline' },
    { key: 'showPredictionAccuracy', label: 'Pred vs Actual', color: '#ff9800', tip: 'Side panel: model-predicted price vs what actually happened (backtracking)' },
    { key: 'showLevelRejection', label: 'Signals', color: '#00bcd4', tip: 'Trade signals from the VM pipeline — level/entry/stop/target lines + win/loss markers' },
  ];

  // Price info
  const lastPrice = data.current_price;
  const priceChange = data.price_change;
  const priceChangePct = data.price_change_percent;
  const isPositive = priceChange >= 0;

  // Initial OHLC values from the most recent candle (live-updated by the WS handler)
  const lastCandle = chartData.candles.length > 0 ? chartData.candles[chartData.candles.length - 1] : null;
  const initOpen = lastCandle ? (lastCandle as any).open : data.current_price;
  const initHigh = lastCandle ? (lastCandle as any).high : data.current_price;
  const initLow = lastCandle ? (lastCandle as any).low : data.current_price;
  const initClose = lastCandle ? (lastCandle as any).close : data.current_price;
  const initVol = chartData.volume.length > 0 ? (chartData.volume[chartData.volume.length - 1] as any).value : null;
  const initIsUp = (initClose ?? 0) >= (initOpen ?? 0);

  return (
    <div ref={wrapperRef} className="w-full h-full flex flex-col" style={{ background: '#131722' }}>
      {/* ─── Chart toolbar ────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-2 py-1 flex-shrink-0" style={{ borderBottom: '1px solid #2a2e39', height: 36 }}>
        {/* Left: Symbol + Price */}
        <div className="flex items-center gap-3">
          {/* Prominent ticker badge so it's always clear which symbol is in view.
              TradingView-style "AAPL · 5m" so the current bar size is glanceable. */}
          <span
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md"
            style={{ background: '#2962ff18', border: '1px solid #2962ff55' }}
          >
            <span className="text-base font-bold tracking-wide" style={{ color: '#2962ff' }}>
              {data.symbol}{barSize ? `, ${barSize}` : ''}
            </span>
            {data.name && data.name !== data.symbol && (
              <span className="text-[10px] hidden lg:inline" style={{ color: '#787b86' }}>{data.name}</span>
            )}
          </span>
          <span className="text-base font-bold" style={{ color: isPositive ? '#26a69a' : '#ef5350' }}>
            <span ref={livePriceRef}>{lastPrice.toFixed(2)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#26a69a' }} />
            <span className="text-[9px]" style={{ color: '#787b86' }}>LIVE</span>
          </span>
          {/* Timezone chip — all chart times are ET (US market timezone).
              Tory asked "is it UTC or ET?" — this removes the guess. */}
          <span
            className="text-[9px] font-semibold px-1.5 py-0.5 rounded"
            style={{ color: '#787b86', background: '#1e222d', border: '1px solid #2a2e39' }}
            title="All times shown are US Eastern (market time)"
          >
            ET
          </span>
          <span className="text-xs" style={{ color: isPositive ? '#26a69a' : '#ef5350' }}>
            {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{priceChangePct.toFixed(2)}%)
          </span>

          {/* OHLC HUD strip — last candle, live-updated by WebSocket */}
          <span
            className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono"
            style={{ background: '#1e222d', border: '1px solid #2a2e39' }}
            title="Open / High / Low / Close / Volume of the current candle"
          >
            <span style={{ color: '#787b86' }}>O</span>
            <span ref={hudOpenRef} style={{ color: '#d1d4dc' }}>{initOpen?.toFixed(2)}</span>
            <span style={{ color: '#787b86' }}>H</span>
            <span ref={hudHighRef} style={{ color: '#26a69a' }}>{initHigh?.toFixed(2)}</span>
            <span style={{ color: '#787b86' }}>L</span>
            <span ref={hudLowRef} style={{ color: '#ef5350' }}>{initLow?.toFixed(2)}</span>
            <span style={{ color: '#787b86' }}>C</span>
            <span ref={hudCloseRef} style={{ color: initIsUp ? '#26a69a' : '#ef5350' }}>{initClose?.toFixed(2)}</span>
            <span style={{ color: '#2a2e39' }}>|</span>
            <span style={{ color: '#787b86' }}>V</span>
            <span ref={hudVolRef} style={{ color: '#d1d4dc' }}>{formatVolume(initVol)}</span>
          </span>

          {/* Signal count widget — visible whenever there are signals for this
              ticker. Split into TWO clickable actions so the Signals Log entry
              point is discoverable (Tory: "where do I click to pull up the
              signals?"). Left half = open the Signals Log panel, right half =
              fit the chart to the signal range. */}
          {data.level_rejection_signals && data.level_rejection_signals.length > 0 && (
            <span
              className="flex items-center text-[10px] overflow-hidden rounded"
              style={{ border: '1px solid #00bcd455', background: '#00bcd418' }}
            >
              <button
                onClick={() => onSignalsLogOpen?.()}
                className="flex items-center gap-1 px-2 py-0.5 hover:bg-[#00bcd428] transition-colors"
                style={{ color: '#00bcd4' }}
                title="Open the Signals Log — full audit trail of signals received from the VM pipeline"
              >
                <span style={{ width: 6, height: 6, borderRadius: 3, background: '#00bcd4', display: 'inline-block' }} />
                <span className="font-semibold">{data.level_rejection_signals.length}</span>
                <span style={{ color: '#00bcd4cc' }}>signal{data.level_rejection_signals.length === 1 ? '' : 's'}</span>
                <span style={{ color: '#00bcd488', fontSize: 9 }} className="ml-1">· open log</span>
              </button>
              <span style={{ width: 1, alignSelf: 'stretch', background: '#00bcd444' }} />
              <button
                onClick={() => fitChartToSignals()}
                className="px-1.5 py-0.5 hover:bg-[#00bcd428] transition-colors"
                style={{ color: '#00bcd4', fontSize: 9 }}
                title="Zoom the chart to the signals' time range"
              >
                ↔ fit
              </button>
            </span>
          )}

          {data.prediction_accuracy && data.prediction_accuracy.resolved > 0 && (
            <span className="flex items-center gap-1.5 px-1.5 py-0.5 rounded text-[10px]" style={{ background: '#1e222d', border: '1px solid #2a2e39' }}>
              <span style={{ color: '#787b86' }}>MAPE</span>
              <span style={{ color: data.prediction_accuracy.mape < 3 ? '#26a69a' : data.prediction_accuracy.mape < 5 ? '#ffb74d' : '#ef5350' }}>
                {data.prediction_accuracy.mape}%
              </span>
              <span style={{ color: '#2a2e39' }}>|</span>
              <span style={{ color: '#787b86' }}>Dir</span>
              <span style={{ color: data.prediction_accuracy.directional_accuracy > 60 ? '#26a69a' : '#ffb74d' }}>
                {data.prediction_accuracy.directional_accuracy}%
              </span>
              <span style={{ color: '#787b86' }}>({data.prediction_accuracy.resolved})</span>
            </span>
          )}
          {fusionSignal && (
            <span
              className="px-1.5 py-0.5 rounded text-[10px] font-bold"
              style={{
                background: fusionSignal.signal === 'BUY' ? '#26a69a22' : fusionSignal.signal === 'SELL' ? '#ef535022' : '#ffb74d22',
                color: fusionSignal.signal === 'BUY' ? '#26a69a' : fusionSignal.signal === 'SELL' ? '#ef5350' : '#ffb74d',
              }}
            >
              {fusionSignal.signal}
            </span>
          )}
        </div>

        {/* Right: Indicator toggles */}
        <div className="flex items-center gap-0.5">
          {indicatorButtons.map((ind) => (
            <button
              key={ind.key}
              onClick={() => toggleFilter(ind.key)}
              title={ind.tip}
              className="px-2 py-1 text-[12px] font-medium rounded transition-all"
              style={{
                background: filters[ind.key] ? `${ind.color}20` : 'transparent',
                color: filters[ind.key] ? ind.color : '#787b86',
                border: filters[ind.key] ? `1px solid ${ind.color}40` : '1px solid transparent',
              }}
            >
              {ind.label}
            </button>
          ))}
        </div>
      </div>

      {/* ─── Chart area ────────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 flex flex-col">
        {/* Main row: candlestick chart + prediction accuracy side panel */}
        <div className="flex-1 min-h-0 flex relative">
          {/* Main chart */}
          <div ref={chartContainerRef} className={filters.showPredictionAccuracy ? 'min-h-0' : 'flex-1 min-h-0'} style={filters.showPredictionAccuracy ? { flex: '7 1 0%', minHeight: 0 } : undefined} />

          {/* Measure tool overlay box (shown while ruler tool is dragging) */}
          <div
            ref={measureBoxRef}
            style={{ display: 'none', position: 'absolute', pointerEvents: 'none', zIndex: 30,
              border: '1px solid #2962ff', background: 'rgba(41, 98, 255, 0.12)' }}
          />
          {/* Measure tool stats popup */}
          <div
            ref={measurePopupRef}
            style={{ display: 'none', position: 'absolute', pointerEvents: 'none', zIndex: 31,
              background: '#1e222d', border: '1px solid #2962ff', borderRadius: 6,
              padding: '6px 10px', fontSize: 11, fontFamily: 'JetBrains Mono, monospace',
              color: '#d1d4dc', whiteSpace: 'nowrap', boxShadow: '0 4px 16px rgba(0,0,0,0.4)' }}
          />

          {/* Predicted vs Actual — right side panel */}
          {filters.showPredictionAccuracy && (
            <div style={{ flex: '3 1 0%', minHeight: 0, borderLeft: '1px solid #2a2e39', display: 'flex', flexDirection: 'column' }}>
              {/* Title bar */}
              <div className="px-3 py-1.5 flex-shrink-0" style={{ background: '#1e222d', borderBottom: '1px solid #2a2e39' }}>
                <div className="text-[11px] font-semibold flex items-center justify-between" style={{ color: '#d1d4dc' }}>
                  <span>Predicted vs Actual</span>
                  {data.prediction_accuracy && data.prediction_accuracy.resolved > 0 && (
                    <span className="text-[10px]" style={{ color: '#787b86' }}>
                      <span style={{ color: data.prediction_accuracy.mape < 3 ? '#26a69a' : data.prediction_accuracy.mape < 5 ? '#ffb74d' : '#ef5350' }}>
                        {data.prediction_accuracy.mape}%
                      </span>
                      {' MAPE · '}
                      <span style={{ color: data.prediction_accuracy.directional_accuracy > 60 ? '#26a69a' : '#ffb74d' }}>
                        {data.prediction_accuracy.directional_accuracy}%
                      </span>
                      {' dir'}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <div className="flex items-center gap-1.5">
                    <span style={{ display: 'inline-block', width: 14, height: 2, background: '#ff9800', borderRadius: 1 }} />
                    <span className="text-[10px]" style={{ color: '#ff9800' }}>Predicted</span>
                    <span className="text-[9px]" style={{ color: '#787b86' }}>(model output)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span style={{ display: 'inline-block', width: 14, height: 8, background: '#4caf5040', border: '1px solid #4caf50', borderRadius: 2 }} />
                    <span className="text-[10px]" style={{ color: '#4caf50' }}>Actual</span>
                    <span className="text-[9px]" style={{ color: '#787b86' }}>(what happened)</span>
                  </div>
                </div>
              </div>
              <div ref={predAccContainerRef} className="flex-1 min-h-0" />
            </div>
          )}

          {/* News tooltip */}
          <div
            ref={tooltipRef}
            style={{
              display: 'none',
              position: 'absolute',
              zIndex: 50,
              maxWidth: 280,
              padding: '8px 10px',
              background: '#1e222d',
              border: '1px solid #2a2e39',
              borderRadius: 6,
              fontSize: 11,
              pointerEvents: 'none',
              boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
            }}
          />
        </div>

        {/* RSI */}
        <div className={filters.showRSI ? '' : 'hidden'} style={{ borderTop: '1px solid #2a2e39' }}>
          <div className="px-2 py-0.5 text-[10px] font-medium" style={{ color: '#7e57c2', background: '#131722' }}>RSI (14)</div>
          <div ref={rsiContainerRef} />
        </div>

        {/* MACD */}
        <div className={filters.showMACD ? '' : 'hidden'} style={{ borderTop: '1px solid #2a2e39' }}>
          <div className="px-2 py-0.5 text-[10px] font-medium" style={{ color: '#2962ff', background: '#131722' }}>MACD (12,26,9)</div>
          <div ref={macdContainerRef} />
        </div>
      </div>
    </div>
  );
});

export default CandlestickChart;
