'use client';

import { useEffect, useRef, useMemo, useCallback, forwardRef, useImperativeHandle } from 'react';
import {
  createChart,
  createSeriesMarkers,
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

function toTime(ts: string): Time {
  return Math.floor(new Date(ts).getTime() / 1000) as Time;
}

// ─────────────────────────────────────────────────────────────────────────

export interface CandlestickChartHandle {
  takeScreenshot: () => void;
  resetView: () => void;
}

interface CandlestickChartProps {
  data: StockData;
  selectedPrediction: PredictionPoint | null;
  onPredictionClick: (prediction: PredictionPoint | null) => void;
  filters: GraphFilters;
  onFilterChange: (filters: GraphFilters) => void;
  fusionSignal?: { signal: string; confidence: number } | null;
  activeTool?: string;
}

const CandlestickChart = forwardRef<CandlestickChartHandle, CandlestickChartProps>(function CandlestickChart({
  data,
  selectedPrediction,
  onPredictionClick,
  filters,
  onFilterChange,
  fusionSignal,
  activeTool = 'crosshair',
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
  }), [data.symbol]);

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
    const rsiVals = computeRSI(closes, Math.min(14, closes.length - 1));
    const macdVals = computeMACD(closes);
    const bb = computeBollingerBands(closes, Math.min(20, Math.floor(closes.length / 2)));

    const sma50Data: LineData[] = [];
    const sma200Data: LineData[] = [];
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

    if ((data.prediction_history || []).length > 0 && candles.length > 0) {
      const candleTimes = candles.map(c => c.time as number);

      // Map: candle unix time -> { predicted, actual } (last write wins)
      const candleMap = new Map<number, { predicted: number; actual: number }>();

      (data.prediction_history || []).forEach((entry: PredictionHistoryEntry) => {
        if (entry.actual_price === null) return;

        const targetStr = entry.target_timestamp || (entry.target_date + 'T16:00:00Z');
        const targetTs = Math.floor(new Date(targetStr).getTime() / 1000);
        if (isNaN(targetTs)) return;

        // Find closest candle
        let bestCandle = candleTimes[0];
        let bestDiff = Math.abs(candleTimes[0] - targetTs);
        for (let i = 1; i < candleTimes.length; i++) {
          const diff = Math.abs(candleTimes[i] - targetTs);
          if (diff < bestDiff) {
            bestDiff = diff;
            bestCandle = candleTimes[i];
          }
        }

        // Only show if within 2 hours of a candle
        if (bestDiff < 7200) {
          candleMap.set(bestCandle, {
            predicted: entry.predicted_price,
            actual: entry.actual_price,
          });
        }
      });

      // Convert map to sorted arrays
      const sortedKeys = Array.from(candleMap.keys()).sort((a, b) => a - b);
      for (const t of sortedKeys) {
        const v = candleMap.get(t)!;
        backtrackPredicted.push({ time: t as unknown as Time, value: v.predicted });
        backtrackActual.push({ time: t as unknown as Time, value: v.actual });
      }
    }

    return {
      candles, volume, sma50Data, sma200Data, bbUpperData, bbLowerData,
      rsiData, macdData, macdSignalData, macdHistData,
      predictionData, upperBoundData, lowerBoundData, markers, newsMarkers,
      backtrackPredicted, backtrackActual,
      currentPrice: closes[closes.length - 1] || 0,
    };
  }, [data]);

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
    const subChartCount = (filters.showRSI ? 1 : 0) + (filters.showMACD ? 1 : 0) + (filters.showPredictionAccuracy ? 1 : 0);
    const subChartHeight = 120;
    const subChartLabelHeight = 20;
    const availableHeight = wrapperHeight - toolbarHeight;
    const mainChartHeight = Math.max(200, availableHeight - subChartCount * (subChartHeight + subChartLabelHeight));

    // ─── TradingView-style colors ────────────────────────────────────
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
      },
    });
    chartRef.current = chart;

    // Candlestick series (TradingView colors)
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

    // Volume (always on - TradingView shows volume by default)
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
            title: `S ${level.price.toFixed(0)}`,
          });
        } catch { /* noop */ }
      });
      (data.resistance_levels || []).forEach((level) => {
        try {
          candleSeries.createPriceLine({
            price: level.price, color: '#ef5350', lineWidth: 1,
            lineStyle: LineStyle.Dashed, axisLabelVisible: true,
            title: `R ${level.price.toFixed(0)}`,
          });
        } catch { /* noop */ }
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

    chart.timeScale().fitContent();

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

    // ─── Prediction Accuracy sub-chart ────────────────────────────────
    if (filters.showPredictionAccuracy && predAccContainerRef.current && (chartData.backtrackPredicted.length > 0 || chartData.backtrackActual.length > 0)) {
      const predAccChart = createChart(predAccContainerRef.current, {
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
      predAccChartRef.current = predAccChart;

      if (chartData.backtrackPredicted.length > 0) {
        const ps = predAccChart.addSeries(LineSeries, { color: '#ff9800', lineWidth: 2, lineStyle: LineStyle.Dashed, title: 'Predicted' });
        ps.setData(chartData.backtrackPredicted);
      }
      if (chartData.backtrackActual.length > 0) {
        const as2 = predAccChart.addSeries(LineSeries, { color: '#4caf50', lineWidth: 2, title: 'Actual' });
        as2.setData(chartData.backtrackActual);
      }

      predAccChart.timeScale().fitContent();
      chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (range) predAccChart.timeScale().setVisibleLogicalRange(range);
      });
    }

    // ─── Resize ──────────────────────────────────────────────────────
    const handleResize = () => {
      if (!chartContainerRef.current || !wrapperRef.current) return;
      const w = chartContainerRef.current.clientWidth;
      const wh = wrapperRef.current.clientHeight;
      const sc = (filters.showRSI ? 1 : 0) + (filters.showMACD ? 1 : 0) + (filters.showPredictionAccuracy ? 1 : 0);
      const mh = Math.max(200, wh - toolbarHeight - sc * (subChartHeight + subChartLabelHeight));
      chart.applyOptions({ width: w, height: mh });
      if (rsiChartRef.current) rsiChartRef.current.applyOptions({ width: w });
      if (macdChartRef.current) macdChartRef.current.applyOptions({ width: w });
      if (predAccChartRef.current) predAccChartRef.current.applyOptions({ width: w });
    };
    window.addEventListener('resize', handleResize);

    // ResizeObserver for container changes
    const ro = new ResizeObserver(handleResize);
    ro.observe(wrapperRef.current);

    return () => {
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
  }, [chartData, filters, data.support_levels, data.resistance_levels, activeTool]);

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
            }

            if (msg.type === 'tick' && livePriceRef.current) {
              livePriceRef.current.textContent = msg.price.toFixed(2);
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

  // Toggle helper
  const toggleFilter = useCallback(
    (key: keyof GraphFilters) => {
      onFilterChange({ ...filters, [key]: !filters[key] });
    },
    [filters, onFilterChange]
  );

  const indicatorButtons: { key: keyof GraphFilters; label: string; color: string }[] = [
    { key: 'showMovingAverages', label: 'MA', color: '#f7a21b' },
    { key: 'showBollingerBands', label: 'BB', color: '#7b1fa2' },
    { key: 'showSupportResistance', label: 'S/R', color: '#26a69a' },
    { key: 'showRSI', label: 'RSI', color: '#7e57c2' },
    { key: 'showMACD', label: 'MACD', color: '#2962ff' },
    { key: 'showPredictedPrice', label: 'Forecast', color: '#42a5f5' },
    { key: 'showConfidenceBounds', label: 'Bounds', color: '#42a5f5' },
    { key: 'showNewsEvents', label: 'News', color: '#ffb74d' },
    { key: 'showPredictionAccuracy', label: 'Pred vs Actual', color: '#ff9800' },
  ];

  // Price info
  const lastPrice = data.current_price;
  const priceChange = data.price_change;
  const priceChangePct = data.price_change_percent;
  const isPositive = priceChange >= 0;

  return (
    <div ref={wrapperRef} className="w-full h-full flex flex-col" style={{ background: '#131722' }}>
      {/* ─── TradingView-style toolbar ─────────────────────────────── */}
      <div className="flex items-center justify-between px-2 py-1 flex-shrink-0" style={{ borderBottom: '1px solid #2a2e39', height: 36 }}>
        {/* Left: Symbol + Price */}
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold" style={{ color: '#d1d4dc' }}>{data.symbol}</span>
          <span className="text-sm font-semibold" style={{ color: isPositive ? '#26a69a' : '#ef5350' }}>
            <span ref={livePriceRef}>{lastPrice.toFixed(2)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#26a69a' }} />
            <span className="text-[9px]" style={{ color: '#787b86' }}>LIVE</span>
          </span>
          <span className="text-xs" style={{ color: isPositive ? '#26a69a' : '#ef5350' }}>
            {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{priceChangePct.toFixed(2)}%)
          </span>
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
              className="px-2 py-0.5 text-[10px] font-medium rounded transition-all"
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
      <div className="flex-1 min-h-0 flex flex-col relative">
        <div ref={chartContainerRef} className="flex-1 min-h-0" />
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

        {/* Predicted vs Actual */}
        <div className={filters.showPredictionAccuracy ? '' : 'hidden'} style={{ borderTop: '1px solid #2a2e39' }}>
          <div className="px-2 py-0.5 text-[10px] font-medium flex items-center gap-3" style={{ background: '#131722' }}>
            <span style={{ color: '#ff9800' }}>● Predicted</span>
            <span style={{ color: '#4caf50' }}>● Actual</span>
            {data.prediction_accuracy && data.prediction_accuracy.resolved > 0 && (
              <span style={{ color: '#787b86' }}>
                MAPE: {data.prediction_accuracy.mape}% | Direction: {data.prediction_accuracy.directional_accuracy}% | {data.prediction_accuracy.resolved} resolved
              </span>
            )}
          </div>
          <div ref={predAccContainerRef} />
        </div>
      </div>
    </div>
  );
});

export default CandlestickChart;
