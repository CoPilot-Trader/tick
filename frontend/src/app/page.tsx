'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { StockData, PredictionPoint, GraphFilters } from '@/types';
import { apiClient } from '@/lib/api/client';
import { formatEasternTime } from '@/lib/time';
import MultiStockSelector from '@/components/MultiStockSelector';
import StockOverview from '@/components/StockOverview';
import CandlestickChart from '@/components/CandlestickChart';
import ComparisonGrid from '@/components/ComparisonGrid';
import PredictionDetail from '@/components/PredictionDetail';
import SignalsLog from '@/components/SignalsLog';
import {
  ChevronDown, LayoutDashboard, Newspaper, Layers, Database, Zap, LineChart, Bell,
  Crosshair, MousePointer2, ZoomIn, ZoomOut, Maximize2, RotateCcw, Camera, Ruler,
  ScrollText, LayoutGrid, Square,
} from 'lucide-react';

const defaultFilters: GraphFilters = {
  showActualPrice: true,
  showPredictedPrice: true,
  showSupportResistance: false,
  showConfidenceBounds: false,
  showVolume: false,
  showRSI: false,
  showMACD: false,
  showBollingerBands: false,
  showMovingAverages: false,
  showEMA9: false,
  showEMA21: false,
  showEMA50: false,
  showNewsEvents: true,
  showTimingSignals: false,
  showPredictionAccuracy: true,
  showLevelRejection: false,
  showVWAP: false,
};

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/fusion', label: 'Trading Signals', icon: Zap },
  { href: '/backtest', label: 'Backtesting', icon: LineChart },
  { href: '/alerts', label: 'Alerts', icon: Bell },
  { href: '/news', label: 'News & Sentiment', icon: Newspaper },
  { href: '/levels', label: 'Support & Resistance', icon: Layers },
  { href: '/pipeline', label: 'Data Pipeline', icon: Database },
];

export default function Home() {
  const [selectedStocks, setSelectedStocks] = useState<string[]>(['AAPL']);
  const [stocksData, setStocksData] = useState<StockData[]>([]);
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionPoint | null>(null);
  const [filters, setFilters] = useState<GraphFilters>(defaultFilters);
  const [loading, setLoading] = useState(true);
  const [navOpen, setNavOpen] = useState(false);
  const [activeChartIndex, setActiveChartIndex] = useState(0);
  const [activeTool, setActiveTool] = useState<string>('crosshair');
  const [activeTimeframe, setActiveTimeframe] = useState<string>('1D'); // RANGE (lookback window)
  const [activeBarSize, setActiveBarSize] = useState<string>('5m');     // BAR SIZE (granularity)
  const [signalsLogOpen, setSignalsLogOpen] = useState(false);
  const [clock, setClock] = useState('');
  const [viewMode, setViewMode] = useState<'single' | 'grid'>('single');
  const chartRef = useRef<{
    takeScreenshot: () => void;
    resetView: () => void;
    fitToSignals: () => void;
    panToSignal: (signalTimeISO: string) => void;
  } | null>(null);

  const loadStocksData = useCallback(async (range: string = activeTimeframe, barSize: string = activeBarSize) => {
    setLoading(true);
    try {
      const data = await Promise.all(
        selectedStocks.map(symbol => apiClient.getStockData(symbol, range, barSize))
      );
      setStocksData(data);
    } catch (error) {
      console.error('Error loading stock data:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedStocks, activeTimeframe, activeBarSize]);

  useEffect(() => {
    if (selectedStocks.length > 0) {
      loadStocksData(activeTimeframe, activeBarSize);
    }
  }, [selectedStocks, activeTimeframe, activeBarSize]);

  // ── Live watchlist tick — every 5s, refresh just the price/change of each
  // selected stock so the comparison tabs feel "alive" (TradingView-style).
  useEffect(() => {
    if (selectedStocks.length === 0) return;

    const refreshTickers = async () => {
      const updates = await Promise.all(
        selectedStocks.map(async (sym) => {
          try {
            const r = await apiClient.getOHLCV(sym, '5m', 1);
            const bars = r?.data || [];
            if (bars.length === 0) return null;
            const last = bars[bars.length - 1];
            const first = bars[0];
            const change = last.close - first.open;
            const changePct = (change / first.open) * 100;
            return { symbol: sym, current_price: last.close, price_change: change, price_change_percent: changePct };
          } catch { return null; }
        })
      );
      setStocksData(prev => prev.map(s => {
        const u = updates.find(x => x?.symbol === s.symbol);
        return u ? { ...s, current_price: u.current_price, price_change: u.price_change, price_change_percent: u.price_change_percent } : s;
      }));
    };

    const interval = setInterval(refreshTickers, 5000);
    return () => clearInterval(interval);
  }, [selectedStocks]);

  const handleTimeframeChange = useCallback((tf: string) => {
    setActiveTimeframe(tf);
  }, []);

  // Live Eastern-time clock (market timezone)
  useEffect(() => {
    const tick = () => setClock(formatEasternTime(new Date(), true));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const handleToolbarAction = useCallback((actionId: string) => {
    const chart = chartRef.current;
    switch (actionId) {
      case 'screenshot':
        chart?.takeScreenshot();
        break;
      case 'reset':
        chart?.resetView();
        break;
      case 'fullscreen':
        document.documentElement.requestFullscreen?.();
        break;
    }
  }, []);

  // Only show the full-screen loader on the initial load (no data yet).
  // Subsequent reloads (timeframe / bar size changes) keep the chart visible
  // with a small inline indicator so the UI never blanks out.
  if (stocksData.length === 0) {
    return (
      <div className="h-screen w-screen flex items-center justify-center" style={{ background: '#131722' }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 mx-auto mb-3" style={{ borderColor: '#2962ff' }}></div>
          <p style={{ color: '#787b86' }}>Loading market data...</p>
        </div>
      </div>
    );
  }

  const isComparisonMode = selectedStocks.length > 1;
  const safeActiveIndex = Math.min(activeChartIndex, stocksData.length - 1);
  const activeStock = stocksData[safeActiveIndex] || stocksData[0];

  // Left sidebar tools
  const tools = [
    { id: 'crosshair', icon: Crosshair, tooltip: 'Crosshair' },
    { id: 'pointer', icon: MousePointer2, tooltip: 'Pointer' },
    { id: 'ruler', icon: Ruler, tooltip: 'Measure' },
  ];

  const actions = [
    { id: 'zoomIn', icon: ZoomIn, tooltip: 'Zoom In' },
    { id: 'zoomOut', icon: ZoomOut, tooltip: 'Zoom Out' },
    { id: 'reset', icon: RotateCcw, tooltip: 'Reset View' },
    { id: 'fullscreen', icon: Maximize2, tooltip: 'Fullscreen' },
    { id: 'screenshot', icon: Camera, tooltip: 'Screenshot' },
  ];

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col" style={{ background: '#131722' }}>
      {/* ─── Top Header ─────────────────────────────────────────────── */}
      <header className="flex-shrink-0 flex items-center gap-2 px-2 py-1" style={{ background: '#1e222d', borderBottom: '1px solid #2a2e39', height: 40 }}>
        {/* Nav dropdown */}
        <div className="relative">
          <button
            onClick={() => setNavOpen(!navOpen)}
            className="flex items-center gap-1.5 px-2 py-1 rounded transition-colors hover:bg-[#2a2e39]"
            style={{ color: '#d1d4dc' }}
          >
            <LayoutDashboard className="w-4 h-4" style={{ color: '#2962ff' }} />
            <span className="text-xs font-semibold hidden sm:inline">TICK</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${navOpen ? 'rotate-180' : ''}`} style={{ color: '#787b86' }} />
          </button>
          {navOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setNavOpen(false)} />
              <div className="absolute left-0 z-50 mt-1 w-48 rounded-lg shadow-2xl overflow-hidden" style={{ background: '#1e222d', border: '1px solid #2a2e39' }}>
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setNavOpen(false)}
                    className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-[#2a2e39]"
                    style={{
                      color: item.href === '/' ? '#d1d4dc' : '#787b86',
                      background: item.href === '/' ? '#2962ff15' : 'transparent',
                      borderLeft: item.href === '/' ? '2px solid #2962ff' : '2px solid transparent',
                    }}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>

        <div style={{ width: 1, height: 20, background: '#2a2e39' }} />

        {/* TICK Branding */}
        <div className="hidden md:block">
          <span className="text-sm font-bold" style={{ color: '#d1d4dc' }}>TICK</span>
          <span className="text-[10px] ml-1.5" style={{ color: '#787b86' }}>Time-Indexed Composite Knowledge</span>
        </div>

        <div className="hidden md:block" style={{ width: 1, height: 20, background: '#2a2e39' }} />

        {/* Stock tabs (multi-stock) — clickable tabs that switch the active chart */}
        {isComparisonMode && (
          <>
            <div className="flex items-center gap-1">
              <span className="text-[8px] uppercase tracking-wider mr-0.5" style={{ color: '#5c6272' }}>Viewing</span>
              {stocksData.map((stock, index) => {
                const isActive = index === safeActiveIndex;
                const isPos = stock.price_change >= 0;
                const dot = ['#2962ff', '#7b1fa2', '#26a69a', '#f7a21b', '#ef5350'][index % 5];
                return (
                  <button
                    key={stock.symbol}
                    onClick={() => setActiveChartIndex(index)}
                    title={isActive ? `${stock.symbol} — currently viewing` : `Click to view ${stock.symbol}`}
                    className="flex items-center gap-1 px-2 py-1 rounded-t text-xs font-semibold transition-all"
                    style={{
                      background: isActive ? '#131722' : '#1a1d28',
                      color: isActive ? '#d1d4dc' : '#787b86',
                      borderBottom: isActive ? '2px solid ' + dot : '2px solid transparent',
                      borderTop: isActive ? '1px solid #2a2e39' : '1px solid transparent',
                      borderLeft: isActive ? '1px solid #2a2e39' : '1px solid transparent',
                      borderRight: isActive ? '1px solid #2a2e39' : '1px solid transparent',
                      opacity: isActive ? 1 : 0.7,
                    }}
                  >
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dot }} />
                    {stock.symbol}
                    <span style={{ color: isPos ? '#26a69a' : '#ef5350', fontSize: 10 }}>
                      {isPos ? '+' : ''}{stock.price_change_percent.toFixed(1)}%
                    </span>
                  </button>
                );
              })}
            </div>
            <div style={{ width: 1, height: 20, background: '#2a2e39' }} />
          </>
        )}

        {/* Stock selector */}
        <div className="flex-1 max-w-xl min-w-0">
          <MultiStockSelector
            selectedStocks={selectedStocks}
            onStocksChange={setSelectedStocks}
            maxStocks={5}
          />
        </div>

        {/* View mode: Single vs Grid comparison (only when 2+ tickers) */}
        {isComparisonMode && (
          <div className="flex items-center gap-0.5 ml-2 flex-shrink-0 rounded" style={{ background: '#131722', border: '1px solid #2a2e39', padding: 2 }}>
            <button
              onClick={() => setViewMode('single')}
              title="Single chart view"
              className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium transition-all"
              style={{ background: viewMode === 'single' ? '#2962ff20' : 'transparent', color: viewMode === 'single' ? '#2962ff' : '#787b86' }}
            >
              <Square className="w-3 h-3" /> Single
            </button>
            <button
              onClick={() => setViewMode('grid')}
              title="Compare all selected tickers in a grid"
              className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium transition-all"
              style={{ background: viewMode === 'grid' ? '#2962ff20' : 'transparent', color: viewMode === 'grid' ? '#2962ff' : '#787b86' }}
            >
              <LayoutGrid className="w-3 h-3" /> Grid
            </button>
          </div>
        )}
      </header>

      {/* ─── Stock Overview Bar ──────────────────────────────────────── */}
      <div className="flex-shrink-0" style={{ borderBottom: '1px solid #2a2e39' }}>
        <StockOverview data={activeStock} />
      </div>

      {/* ─── Main Area: Left Toolbar + Chart ─────────────────────────── */}
      <div className="flex-1 min-h-0 flex">
        {/* Left Toolbar */}
        <div className="flex-shrink-0 flex flex-col items-center py-2 px-1 gap-0.5" style={{ background: '#1e222d', borderRight: '1px solid #2a2e39', width: 40 }}>
          {/* Tool buttons */}
          {tools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => setActiveTool(tool.id)}
              className="w-8 h-8 flex items-center justify-center rounded transition-all"
              style={{
                background: activeTool === tool.id ? '#2962ff20' : 'transparent',
                color: activeTool === tool.id ? '#2962ff' : '#787b86',
              }}
              title={tool.tooltip}
            >
              <tool.icon className="w-4 h-4" />
            </button>
          ))}

          {/* Separator */}
          <div className="my-1" style={{ width: 20, height: 1, background: '#2a2e39' }} />

          {/* Action buttons */}
          {actions.map((action) => (
            <button
              key={action.id}
              onClick={() => handleToolbarAction(action.id)}
              className="w-8 h-8 flex items-center justify-center rounded transition-all hover:bg-[#2a2e39]"
              style={{ color: '#787b86' }}
              title={action.tooltip}
            >
              <action.icon className="w-4 h-4" />
            </button>
          ))}

          {/* Spacer */}
          <div className="flex-1" />
        </div>

        {/* Chart Area — single chart or comparison grid */}
        <div className="flex-1 min-h-0 min-w-0">
          {isComparisonMode && viewMode === 'grid' ? (
            <ComparisonGrid
              stocks={stocksData}
              activeIndex={safeActiveIndex}
              onSelect={(i) => { setActiveChartIndex(i); setViewMode('single'); }}
            />
          ) : (
            <CandlestickChart
              ref={chartRef}
              key={`${activeStock.symbol}-${activeTimeframe}-${activeBarSize}`}
              data={activeStock}
              selectedPrediction={selectedPrediction}
              onPredictionClick={setSelectedPrediction}
              filters={filters}
              onFilterChange={setFilters}
              activeTool={activeTool}
              onSignalsLogOpen={() => setSignalsLogOpen(true)}
              barSize={({ '1d': 'D', '1wk': 'W' } as Record<string, string>)[activeBarSize] || activeBarSize}
            />
          )}
        </div>
      </div>

      {/* ─── Bottom Toolbar ──────────────────────────────────────────── */}
      <div className="flex-shrink-0 flex items-center justify-between px-3" style={{ background: '#1e222d', borderTop: '1px solid #2a2e39', height: 28 }}>
        <div className="flex items-center gap-3">
          {/* Range selector — lookback window. Combines with bar size below. */}
          <div className="flex items-center gap-0.5">
            <span className="text-[9px] mr-1" style={{ color: '#5c6272' }}>RANGE</span>
            {['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'All'].map((tf) => (
              <button
                key={tf}
                onClick={() => handleTimeframeChange(tf)}
                className="px-2 py-0.5 text-[10px] font-medium rounded transition-all hover:bg-[#2a2e39]"
                style={{ color: tf === activeTimeframe ? '#2962ff' : '#787b86' }}
                title={`Lookback window: ${tf} (combines with the selected bar size)`}
              >
                {tf}
              </button>
            ))}
          </div>

          <div style={{ width: 1, height: 16, background: '#2a2e39' }} />

          {/* Bar size selector — candle granularity. Combines with range above. */}
          <div className="flex items-center gap-0.5">
            <span className="text-[9px] mr-1" style={{ color: '#5c6272' }}>BAR</span>
            {loading && (
              <div className="animate-spin rounded-full h-2.5 w-2.5 border-b mr-1" style={{ borderColor: '#2962ff' }} title="Refreshing data..." />
            )}
            {[
              { key: '1m', label: '1m', smartRange: '1D' },
              { key: '5m', label: '5m', smartRange: '5D' },
              { key: '15m', label: '15m', smartRange: '1M' },
              // 30m smart-range was '6M' in Tory's spec, but yfinance only
              // surfaces ~50 days of 30m bars — so 6M would silently clamp.
              // 1M aligns the default with what the source can actually give.
              { key: '30m', label: '30m', smartRange: '1M' },
              { key: '1h', label: '1h', smartRange: '1Y' },
              { key: '1d', label: 'D', smartRange: '1Y' },   // Tory's spec
              { key: '1wk', label: 'W', smartRange: 'All' },
            ].map((b) => (
              <button
                key={b.key}
                onClick={() => {
                  // Smart default: picking a bar size auto-sets a sensible lookback
                  // window for that granularity (e.g. Daily → 1Y, 30m → 6M). The user
                  // can still override the range manually afterward.
                  setActiveBarSize(b.key);
                  setActiveTimeframe(b.smartRange);
                }}
                className="px-2 py-0.5 text-[10px] font-medium rounded transition-all hover:bg-[#2a2e39]"
                style={{ color: activeBarSize === b.key ? '#26a69a' : '#787b86' }}
                title={`${b.label} candles · default lookback ${b.smartRange} (you can override the range manually)`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSignalsLogOpen(true)}
            className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded transition-all hover:bg-[#2a2e39]"
            style={{ color: '#00bcd4', border: '1px solid #00bcd440' }}
            title="Audit log of signals received from the VM pipeline"
          >
            <ScrollText className="w-3 h-3" />
            Signals Log
          </button>
          <span className="text-[10px]" style={{ color: '#787b86' }}>
            {clock} ET
          </span>
        </div>
      </div>

      {/* Prediction Detail Modal */}
      {selectedPrediction && (
        <PredictionDetail
          prediction={selectedPrediction}
          onClose={() => setSelectedPrediction(null)}
        />
      )}

      {/* Signals Log slide-in */}
      <SignalsLog
        symbol={activeStock.symbol}
        open={signalsLogOpen}
        onClose={() => setSignalsLogOpen(false)}
        onSignalClick={(ts) => chartRef.current?.panToSignal(ts)}
      />
    </div>
  );
}
