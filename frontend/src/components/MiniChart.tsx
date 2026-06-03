'use client';

import { useEffect, useRef } from 'react';
import {
  createChart, ColorType, CandlestickSeries, type IChartApi, type Time,
} from 'lightweight-charts';
import { StockData } from '@/types';
import { formatEasternAxis } from '@/lib/time';

interface MiniChartProps {
  data: StockData;
  active?: boolean;
  onClick?: () => void;
}

/**
 * Compact single-ticker candlestick chart used in the comparison grid.
 * Deliberately lightweight: candles + volume only, no overlays/sub-panels.
 */
export default function MiniChart({ data, active, onClick }: MiniChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;

    const chart = createChart(el, {
      width: el.clientWidth,
      height: el.clientHeight,
      layout: {
        background: { type: ColorType.Solid, color: '#131722' },
        textColor: '#787b86',
        fontSize: 10,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      },
      localization: { timeFormatter: (t: number) => formatEasternAxis(t, true) },
      grid: { vertLines: { color: '#1e222d' }, horzLines: { color: '#1e222d' } },
      rightPriceScale: { borderColor: '#2a2e39', scaleMargins: { top: 0.1, bottom: 0.1 } },
      timeScale: {
        borderColor: '#2a2e39', timeVisible: true, secondsVisible: false,
        tickMarkFormatter: (t: number, tickMarkType: number) => formatEasternAxis(t, true, tickMarkType),
      },
      handleScroll: true,
      handleScale: true,
    } as any);
    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a', downColor: '#ef5350',
      borderUpColor: '#26a69a', borderDownColor: '#ef5350',
      wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });

    const candles = (data.historical_data || []).map((p) => ({
      time: Math.floor(new Date(p.timestamp).getTime() / 1000) as Time,
      open: p.open, high: p.high, low: p.low, close: p.close,
    }));
    candleSeries.setData(candles);
    chart.timeScale().fitContent();

    const handleResize = () => {
      if (!containerRef.current) return;
      chart.applyOptions({ width: containerRef.current.clientWidth, height: containerRef.current.clientHeight });
    };
    const ro = new ResizeObserver(handleResize);
    ro.observe(el);
    window.addEventListener('resize', handleResize);

    return () => {
      ro.disconnect();
      window.removeEventListener('resize', handleResize);
      try { chart.remove(); } catch { /* noop */ }
      chartRef.current = null;
    };
  }, [data.symbol, data.historical_data]);

  const isPos = data.price_change >= 0;

  return (
    <div
      onClick={onClick}
      className="flex flex-col cursor-pointer transition-all"
      style={{
        background: '#131722',
        border: active ? '1px solid #2962ff' : '1px solid #2a2e39',
        borderRadius: 6,
        overflow: 'hidden',
        minHeight: 0,
      }}
      title={`Click to open ${data.symbol} in full view`}
    >
      {/* Mini header */}
      <div className="flex items-center justify-between px-2 py-1 flex-shrink-0" style={{ background: '#1a1d28', borderBottom: '1px solid #2a2e39' }}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold" style={{ color: '#2962ff' }}>{data.symbol}</span>
          <span className="text-xs font-semibold" style={{ color: '#d1d4dc' }}>{data.current_price.toFixed(2)}</span>
        </div>
        <span className="text-[10px] font-semibold" style={{ color: isPos ? '#26a69a' : '#ef5350' }}>
          {isPos ? '+' : ''}{data.price_change.toFixed(2)} ({isPos ? '+' : ''}{data.price_change_percent.toFixed(2)}%)
        </span>
      </div>
      {/* Chart */}
      <div ref={containerRef} className="flex-1 min-h-0" />
    </div>
  );
}
