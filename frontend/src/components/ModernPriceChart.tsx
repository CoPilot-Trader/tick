'use client';

import { useMemo, useState, useRef, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Dot,
  Area,
  AreaChart,
  Bar,
  BarChart,
  ComposedChart,
  Brush,
} from 'recharts';
import { StockData, PredictionPoint, GraphFilters } from '@/types';
import { format } from 'date-fns';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import GraphFiltersComponent from './GraphFilters';

// ── Technical indicator helpers ──────────────────────────────────────────────

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

function computeMACD(closes: number[]): { macd: (number | null)[]; signal: (number | null)[]; histogram: (number | null)[] } {
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
  // Signal line: 9-period EMA of MACD
  const nonNull = macdLine.filter(v => v !== null) as number[];
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

function computeBollingerBands(closes: number[], period = 20, stdDev = 2): { upper: (number | null)[]; lower: (number | null)[] } {
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

// ─────────────────────────────────────────────────────────────────────────────

interface ModernPriceChartProps {
  data: StockData;
  selectedPrediction: PredictionPoint | null;
  onPredictionClick: (prediction: PredictionPoint | null) => void;
  filters: GraphFilters;
  onFilterChange: (filters: GraphFilters) => void;
}

interface ChartDataPoint {
  timestamp: string;
  time: string;
  actual: number | null;
  predicted: number | null;
  upper_bound: number | null;
  lower_bound: number | null;
  volume: number | null;
  rsi: number | null;
  macd: number | null;
  bb_upper: number | null;
  bb_lower: number | null;
  sma_50: number | null;
  sma_200: number | null;
  isPrediction: boolean;
  hasNews: boolean;
  timingScore: number | null;
  prediction?: PredictionPoint;
}

interface SelectionBox {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export default function ModernPriceChart({
  data,
  selectedPrediction,
  onPredictionClick,
  filters,
  onFilterChange,
}: ModernPriceChartProps) {
  const [zoomStart, setZoomStart] = useState<number | null>(null);
  const [zoomEnd, setZoomEnd] = useState<number | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionBox, setSelectionBox] = useState<SelectionBox | null>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  const chartData = useMemo(() => {
    const points: ChartDataPoint[] = [];
    const now = new Date();
    const today = new Date();

    const historical = data.historical_data;
    const closes = historical.map(p => p.close);

    // Pre-compute indicators from historical close prices
    const sma50 = sma(closes, Math.min(50, Math.floor(closes.length / 2)));
    const sma200 = sma(closes, Math.min(200, closes.length));
    const rsiValues = computeRSI(closes, Math.min(14, closes.length - 1));
    const macdValues = computeMACD(closes);
    const bb = computeBollingerBands(closes, Math.min(20, Math.floor(closes.length / 2)));

    // Add historical data with computed indicators
    historical.forEach((point, i) => {
      const pointDate = new Date(point.timestamp);
      const isToday = pointDate.toDateString() === today.toDateString();
      points.push({
        timestamp: point.timestamp,
        time: isToday ? format(pointDate, 'HH:mm') : format(pointDate, 'MM/dd HH:mm'),
        actual: point.close,
        predicted: null,
        upper_bound: null,
        lower_bound: null,
        volume: point.volume,
        rsi: rsiValues[i] ?? null,
        macd: macdValues.macd[i] ?? null,
        bb_upper: bb.upper[i] ?? null,
        bb_lower: bb.lower[i] ?? null,
        sma_50: sma50[i] ?? null,
        sma_200: sma200[i] ?? null,
        isPrediction: false,
        hasNews: false,
        timingScore: null,
      });
    });

    // Carry forward last indicator values for transition + prediction points
    const lastIdx = closes.length - 1;
    const lastSma50 = sma50[lastIdx] ?? null;
    const lastSma200 = sma200[lastIdx] ?? null;
    const lastRsi = rsiValues[lastIdx] ?? null;
    const lastMacd = macdValues.macd[lastIdx] ?? null;
    const lastBbUpper = bb.upper[lastIdx] ?? null;
    const lastBbLower = bb.lower[lastIdx] ?? null;

    // Add current point (transition from actual to predicted)
    const lastActual = historical[historical.length - 1];
    if (lastActual) {
      const firstPrediction = data.predictions[0];
      if (firstPrediction) {
        const nowIsToday = now.toDateString() === today.toDateString();
        points.push({
          timestamp: now.toISOString(),
          time: nowIsToday ? format(now, 'HH:mm') : format(now, 'MM/dd HH:mm'),
          actual: lastActual.close,
          predicted: firstPrediction.predicted_price,
          upper_bound: firstPrediction.upper_bound,
          lower_bound: firstPrediction.lower_bound,
          volume: lastActual.volume,
          rsi: lastRsi,
          macd: lastMacd,
          bb_upper: lastBbUpper,
          bb_lower: lastBbLower,
          sma_50: lastSma50,
          sma_200: lastSma200,
          isPrediction: true,
          hasNews: (firstPrediction.news_events?.length || 0) > 0,
          timingScore: firstPrediction.timing_score || null,
          prediction: firstPrediction,
        });
      }
    }

    // Add all prediction points (6 points at 10-min intervals for 1 hour)
    data.predictions.forEach((prediction) => {
      const predDate = new Date(prediction.timestamp);
      const isToday = predDate.toDateString() === today.toDateString();
      points.push({
        timestamp: prediction.timestamp,
        time: isToday ? format(predDate, 'HH:mm') : format(predDate, 'MM/dd HH:mm'),
        actual: null,
        predicted: prediction.predicted_price,
        upper_bound: prediction.upper_bound,
        lower_bound: prediction.lower_bound,
        volume: null,
        rsi: lastRsi,
        macd: lastMacd,
        bb_upper: lastBbUpper,
        bb_lower: lastBbLower,
        sma_50: lastSma50,
        sma_200: lastSma200,
        isPrediction: true,
        hasNews: (prediction.news_events?.length || 0) > 0,
        timingScore: prediction.timing_score || null,
        prediction,
      });
    });

    return points;
  }, [data]);

  // Apply zoom if set
  const displayedData = useMemo(() => {
    if (zoomStart === null || zoomEnd === null) return chartData;
    return chartData.slice(zoomStart, zoomEnd + 1);
  }, [chartData, zoomStart, zoomEnd]);

  // Support and resistance levels
  const supportLevels = data.support_levels.map(level => level.price);
  const resistanceLevels = data.resistance_levels.map(level => level.price);

  // Mouse event handlers for selection box
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return; // Only left mouse button
    const rect = chartContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsSelecting(true);
    setSelectionBox({
      startX: x,
      startY: y,
      endX: x,
      endY: y,
    });
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!isSelecting || !selectionBox) return;
    const rect = chartContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setSelectionBox({
      ...selectionBox,
      endX: x,
      endY: y,
    });
  }, [isSelecting, selectionBox]);

  const handleMouseUp = useCallback(() => {
    if (!isSelecting || !selectionBox) return;

    const rect = chartContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    // Calculate selection bounds
    const minX = Math.min(selectionBox.startX, selectionBox.endX);
    const maxX = Math.max(selectionBox.startX, selectionBox.endX);

    // Only zoom if selection is meaningful (at least 50px wide)
    if (maxX - minX > 50) {
      // Calculate which data points are in the selection
      // Account for padding and margins
      const containerPadding = 16; // p-4 = 16px
      const leftMargin = 60; // Y-axis width
      const rightMargin = 20; // Right margin
      const bottomMargin = 50; // For brush/axis
      
      const chartAreaLeft = containerPadding + leftMargin;
      const chartAreaRight = rect.width - containerPadding - rightMargin;
      const chartAreaWidth = chartAreaRight - chartAreaLeft;
      
      // Calculate relative positions within chart area
      const relativeMinX = Math.max(0, minX - chartAreaLeft);
      const relativeMaxX = Math.min(chartAreaWidth, maxX - chartAreaLeft);

      // Map to data indices
      const startIndex = Math.floor((relativeMinX / chartAreaWidth) * chartData.length);
      const endIndex = Math.ceil((relativeMaxX / chartAreaWidth) * chartData.length);

      // Ensure valid indices
      const validStart = Math.max(0, Math.min(startIndex, chartData.length - 1));
      const validEnd = Math.max(validStart + 1, Math.min(endIndex, chartData.length));

      if (validStart < validEnd) {
        setZoomStart(validStart);
        setZoomEnd(validEnd - 1);
      }
    }

    setIsSelecting(false);
    setSelectionBox(null);
  }, [isSelecting, selectionBox, chartData.length]);

  const handleZoomIn = () => {
    if (zoomStart === null || zoomEnd === null) {
      // Zoom to middle 50%
      const start = Math.floor(chartData.length * 0.25);
      const end = Math.floor(chartData.length * 0.75);
      setZoomStart(start);
      setZoomEnd(end);
    } else {
      // Zoom in further (reduce range by 20%)
      const range = zoomEnd - zoomStart;
      const newRange = Math.floor(range * 0.8);
      const center = Math.floor((zoomStart + zoomEnd) / 2);
      const newStart = Math.max(0, center - Math.floor(newRange / 2));
      const newEnd = Math.min(chartData.length - 1, newStart + newRange);
      setZoomStart(newStart);
      setZoomEnd(newEnd);
    }
  };

  const handleZoomOut = () => {
    if (zoomStart === null || zoomEnd === null) return;
    
    const range = zoomEnd - zoomStart;
    const newRange = Math.floor(range * 1.2);
    const center = Math.floor((zoomStart + zoomEnd) / 2);
    const newStart = Math.max(0, center - Math.floor(newRange / 2));
    const newEnd = Math.min(chartData.length - 1, newStart + newRange);
    
    if (newStart === 0 && newEnd === chartData.length - 1) {
      // Reset zoom
      setZoomStart(null);
      setZoomEnd(null);
    } else {
      setZoomStart(newStart);
      setZoomEnd(newEnd);
    }
  };

  const handleResetZoom = () => {
    setZoomStart(null);
    setZoomEnd(null);
  };

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload.isPrediction || !filters.showPredictedPrice) return null;

    const isSelected = selectedPrediction?.timestamp === payload.timestamp;
    const hasNews = payload.hasNews;
    
    return (
      <g>
        <Dot
          cx={cx}
          cy={cy}
          r={isSelected ? 8 : hasNews ? 6 : 4}
          fill={isSelected ? '#0ea5e9' : hasNews ? '#f59e0b' : '#8b5cf6'}
          stroke={isSelected ? '#0284c7' : hasNews ? '#d97706' : '#6d28d9'}
          strokeWidth={isSelected ? 3 : hasNews ? 2 : 1}
          onClick={() => onPredictionClick(payload.prediction)}
          style={{ cursor: 'pointer' }}
        />
        {hasNews && (
          <circle
            cx={cx}
            cy={cy}
            r={isSelected ? 10 : 8}
            fill="none"
            stroke="#f59e0b"
            strokeWidth={1}
            strokeDasharray="3 3"
            opacity={0.5}
          />
        )}
      </g>
    );
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">{data.time}</p>
        {data.actual !== null && (
          <p className="text-sm font-semibold text-blue-400">
            Actual: ${data.actual.toFixed(2)}
          </p>
        )}
        {data.predicted !== null && (
          <p className="text-sm font-semibold text-purple-400">
            Predicted: ${data.predicted.toFixed(2)}
          </p>
        )}
        {data.sma_50 !== null && filters.showMovingAverages && (
          <p className="text-xs text-amber-400">SMA 50: ${data.sma_50.toFixed(2)}</p>
        )}
        {data.sma_200 !== null && filters.showMovingAverages && (
          <p className="text-xs text-pink-400">SMA 200: ${data.sma_200.toFixed(2)}</p>
        )}
        {data.bb_upper !== null && filters.showBollingerBands && (
          <p className="text-xs text-purple-300">BB: ${data.bb_lower?.toFixed(2)} - ${data.bb_upper.toFixed(2)}</p>
        )}
        {data.rsi !== null && filters.showRSI && (
          <p className="text-xs text-cyan-400">RSI: {data.rsi.toFixed(1)}</p>
        )}
        {data.macd !== null && filters.showMACD && (
          <p className="text-xs text-green-400">MACD: {data.macd.toFixed(3)}</p>
        )}
        {data.volume !== null && filters.showVolume && (
          <p className="text-xs text-gray-400">Vol: {data.volume.toLocaleString()}</p>
        )}
        {data.hasNews && (
          <p className="text-xs text-amber-400 mt-1">News Event</p>
        )}
      </div>
    );
  };

  // Calculate selection box dimensions
  const selectionStyle = selectionBox ? {
    left: `${Math.min(selectionBox.startX, selectionBox.endX)}px`,
    top: `${Math.min(selectionBox.startY, selectionBox.endY)}px`,
    width: `${Math.abs(selectionBox.endX - selectionBox.startX)}px`,
    height: `${Math.abs(selectionBox.endY - selectionBox.startY)}px`,
  } : {};

  return (
    <div 
      ref={chartContainerRef}
      className="w-full h-full bg-gray-900 border border-gray-800 rounded-lg p-2 sm:p-4 flex flex-col relative"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ userSelect: 'none', cursor: isSelecting ? 'crosshair' : 'default' }}
    >
      {/* Selection Box Overlay */}
      {selectionBox && (
        <div
          className="absolute border-2 border-primary-500 bg-primary-500/20 pointer-events-none z-10 rounded"
          style={selectionStyle}
        />
      )}

      {/* Header with Filters and Zoom Controls */}
      <div className="mb-2 sm:mb-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 z-20 relative">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 sm:gap-3 mb-1.5 sm:mb-2">
            <h3 className="text-xs sm:text-sm font-semibold text-white whitespace-nowrap">{data.symbol} Price Chart</h3>
            <span className="text-xs text-gray-400 hidden sm:inline">
              {zoomStart !== null && zoomEnd !== null
                ? `${displayedData.length} points (zoomed)`
                : `${chartData.length} points`}
            </span>
            <span className="text-xs text-gray-500 hidden md:inline">
              {isSelecting ? 'Release to zoom' : 'Click and drag on chart to zoom'}
            </span>
          </div>
          <GraphFiltersComponent filters={filters} onFilterChange={onFilterChange} />
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2 sm:ml-4 flex-shrink-0">
          <button
            onClick={handleZoomIn}
            className="p-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            disabled={zoomStart === null || zoomEnd === null}
            className="p-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetZoom}
            disabled={zoomStart === null || zoomEnd === null}
            className="p-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Reset Zoom"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Charts */}
      <div className="flex-1 min-h-0 relative flex flex-col gap-1">
        {/* Main Price Chart */}
        <div className={`${filters.showRSI || filters.showMACD ? 'flex-[3]' : 'flex-1'} min-h-0`}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={displayedData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="predictedGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />

              <XAxis
                dataKey="time"
                stroke="#6b7280"
                fontSize={11}
                tick={{ fill: '#9ca3af' }}
                axisLine={{ stroke: '#374151' }}
                interval="preserveStartEnd"
              />

              <YAxis
                yAxisId="price"
                stroke="#6b7280"
                fontSize={11}
                tick={{ fill: '#9ca3af' }}
                axisLine={{ stroke: '#374151' }}
                domain={['dataMin - 2', 'dataMax + 2']}
                width={60}
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />

              {filters.showVolume && (
                <YAxis
                  yAxisId="volume"
                  orientation="right"
                  stroke="#6b7280"
                  fontSize={11}
                  tick={{ fill: '#9ca3af' }}
                  axisLine={{ stroke: '#374151' }}
                  width={50}
                  tickFormatter={(value) => {
                    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
                    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
                    return value.toString();
                  }}
                />
              )}

              <Tooltip content={<CustomTooltip />} />

              {/* Support levels */}
              {filters.showSupportResistance && supportLevels.map((level, index) => (
                <ReferenceLine
                  key={`support-${index}`}
                  yAxisId="price"
                  y={level}
                  stroke="#22c55e"
                  strokeDasharray="4 4"
                  strokeOpacity={0.6}
                  label={{ value: `S ${level.toFixed(0)}`, position: 'right', fill: '#22c55e', fontSize: 10 }}
                />
              ))}

              {/* Resistance levels */}
              {filters.showSupportResistance && resistanceLevels.map((level, index) => (
                <ReferenceLine
                  key={`resistance-${index}`}
                  yAxisId="price"
                  y={level}
                  stroke="#ef4444"
                  strokeDasharray="4 4"
                  strokeOpacity={0.6}
                  label={{ value: `R ${level.toFixed(0)}`, position: 'right', fill: '#ef4444', fontSize: 10 }}
                />
              ))}

              {/* Moving Averages */}
              {filters.showMovingAverages && (
                <>
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="sma_50"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray="3 3"
                    name="SMA 50"
                    connectNulls={false}
                  />
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="sma_200"
                    stroke="#ec4899"
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray="3 3"
                    name="SMA 200"
                    connectNulls={false}
                  />
                </>
              )}

              {/* Bollinger Bands */}
              {filters.showBollingerBands && (
                <>
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="bb_upper"
                    stroke="#a78bfa"
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="2 2"
                    strokeOpacity={0.6}
                    name="BB Upper"
                    connectNulls={false}
                  />
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="bb_lower"
                    stroke="#a78bfa"
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="2 2"
                    strokeOpacity={0.6}
                    name="BB Lower"
                    connectNulls={false}
                  />
                </>
              )}

              {/* Actual price area */}
              {filters.showActualPrice && (
                <Area
                  yAxisId="price"
                  type="monotone"
                  dataKey="actual"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  fill="url(#actualGradient)"
                  name="Actual Price"
                  connectNulls={false}
                />
              )}

              {/* Predicted price area */}
              {filters.showPredictedPrice && (
                <Area
                  yAxisId="price"
                  type="monotone"
                  dataKey="predicted"
                  stroke="#8b5cf6"
                  strokeWidth={2.5}
                  strokeDasharray="0"
                  fill="url(#predictedGradient)"
                  dot={<CustomDot />}
                  name="Predicted Price"
                  connectNulls={true}
                />
              )}

              {/* Confidence bounds */}
              {filters.showConfidenceBounds && filters.showPredictedPrice && (
                <>
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="upper_bound"
                    stroke="#8b5cf6"
                    strokeWidth={1}
                    strokeDasharray="2 2"
                    dot={false}
                    strokeOpacity={0.4}
                    name="Upper Bound"
                    connectNulls={true}
                  />
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="lower_bound"
                    stroke="#8b5cf6"
                    strokeWidth={1}
                    strokeDasharray="2 2"
                    dot={false}
                    strokeOpacity={0.4}
                    name="Lower Bound"
                    connectNulls={true}
                  />
                </>
              )}

              {/* Volume bars */}
              {filters.showVolume && (
                <Bar
                  yAxisId="volume"
                  dataKey="volume"
                  fill="#374151"
                  opacity={0.3}
                  name="Volume"
                />
              )}

              {/* Brush for timeline navigation */}
              <Brush
                dataKey="time"
                height={30}
                stroke="#4b5563"
                fill="#1f2937"
                startIndex={zoomStart || 0}
                endIndex={zoomEnd !== null ? zoomEnd : chartData.length - 1}
                onChange={(brushData: any) => {
                  if (brushData && brushData.startIndex !== undefined && brushData.endIndex !== undefined) {
                    setZoomStart(brushData.startIndex);
                    setZoomEnd(brushData.endIndex);
                  }
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* RSI Sub-panel */}
        {filters.showRSI && (
          <div className="flex-1 min-h-[80px] max-h-[120px] border-t border-gray-800">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={displayedData} margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" hide />
                <YAxis
                  domain={[0, 100]}
                  width={60}
                  stroke="#6b7280"
                  fontSize={10}
                  tick={{ fill: '#9ca3af' }}
                  ticks={[30, 50, 70]}
                />
                <Tooltip
                  content={({ active, payload }: any) => {
                    if (!active || !payload?.[0]) return null;
                    const rsi = payload[0].payload.rsi;
                    return rsi !== null ? (
                      <div className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-cyan-400">
                        RSI: {rsi.toFixed(1)}
                      </div>
                    ) : null;
                  }}
                />
                {/* Overbought/Oversold zones */}
                <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />
                <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" strokeOpacity={0.5} />
                <Area
                  type="monotone"
                  dataKey="rsi"
                  stroke="#06b6d4"
                  strokeWidth={1.5}
                  fill="#06b6d4"
                  fillOpacity={0.1}
                  dot={false}
                  connectNulls={false}
                  name="RSI"
                />
                <text x={65} y={15} fill="#9ca3af" fontSize={10}>RSI (14)</text>
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* MACD Sub-panel */}
        {filters.showMACD && (
          <div className="flex-1 min-h-[80px] max-h-[120px] border-t border-gray-800">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={displayedData} margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" hide />
                <YAxis
                  width={60}
                  stroke="#6b7280"
                  fontSize={10}
                  tick={{ fill: '#9ca3af' }}
                  tickFormatter={(v) => v.toFixed(1)}
                />
                <Tooltip
                  content={({ active, payload }: any) => {
                    if (!active || !payload?.[0]) return null;
                    const macd = payload[0].payload.macd;
                    return macd !== null ? (
                      <div className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-green-400">
                        MACD: {macd.toFixed(3)}
                      </div>
                    ) : null;
                  }}
                />
                <ReferenceLine y={0} stroke="#4b5563" />
                <Line
                  type="monotone"
                  dataKey="macd"
                  stroke="#22c55e"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                  name="MACD"
                />
                <text x={65} y={15} fill="#9ca3af" fontSize={10}>MACD (12,26,9)</text>
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
