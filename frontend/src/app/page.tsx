'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { StockData, PredictionPoint, GraphFilters } from '@/types';
import { apiClient } from '@/lib/api/client';
import MultiStockSelector from '@/components/MultiStockSelector';
import StockOverview from '@/components/StockOverview';
import CandlestickChart from '@/components/CandlestickChart';
import PredictionDetail from '@/components/PredictionDetail';
import {
  ChevronDown, LayoutDashboard, Newspaper, Layers, Database, Zap, LineChart, Bell,
  Crosshair, MousePointer2, ZoomIn, ZoomOut, Maximize2, RotateCcw, Camera, Ruler,
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
  showNewsEvents: true,
  showTimingSignals: false,
  showPredictionAccuracy: true,
  showLevelRejection: false,
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
  const [activeTimeframe, setActiveTimeframe] = useState<string>('1D');
  const chartRef = useRef<{ takeScreenshot: () => void; resetView: () => void } | null>(null);

  const loadStocksData = useCallback(async (range: string = activeTimeframe) => {
    setLoading(true);
    try {
      const data = await Promise.all(
        selectedStocks.map(symbol => apiClient.getStockData(symbol, range))
      );
      setStocksData(data);
    } catch (error) {
      console.error('Error loading stock data:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedStocks, activeTimeframe]);

  useEffect(() => {
    if (selectedStocks.length > 0) {
      loadStocksData(activeTimeframe);
    }
  }, [selectedStocks, activeTimeframe]);

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

  if (loading || stocksData.length === 0) {
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

        {/* Stock tabs (multi-stock) */}
        {isComparisonMode && (
          <>
            <div className="flex items-center gap-0.5">
              {stocksData.map((stock, index) => {
                const isActive = index === safeActiveIndex;
                const isPos = stock.price_change >= 0;
                return (
                  <button
                    key={stock.symbol}
                    onClick={() => setActiveChartIndex(index)}
                    className="flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium transition-all"
                    style={{
                      background: isActive ? '#2a2e39' : 'transparent',
                      color: isActive ? '#d1d4dc' : '#787b86',
                    }}
                  >
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: ['#2962ff', '#7b1fa2', '#26a69a', '#f7a21b', '#ef5350'][index % 5] }} />
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

        {/* Chart Area */}
        <div className="flex-1 min-h-0 min-w-0">
          <CandlestickChart
            ref={chartRef}
            key={`${activeStock.symbol}-${activeTimeframe}`}
            data={activeStock}
            selectedPrediction={selectedPrediction}
            onPredictionClick={setSelectedPrediction}
            filters={filters}
            onFilterChange={setFilters}
            activeTool={activeTool}
          />
        </div>
      </div>

      {/* ─── Bottom Toolbar ──────────────────────────────────────────── */}
      <div className="flex-shrink-0 flex items-center justify-between px-3" style={{ background: '#1e222d', borderTop: '1px solid #2a2e39', height: 28 }}>
        <div className="flex items-center gap-1">
          {['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'All'].map((tf) => (
            <button
              key={tf}
              onClick={() => handleTimeframeChange(tf)}
              className="px-2 py-0.5 text-[10px] font-medium rounded transition-all hover:bg-[#2a2e39]"
              style={{ color: tf === activeTimeframe ? '#2962ff' : '#787b86' }}
            >
              {tf}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px]" style={{ color: '#787b86' }}>
            {new Date().toLocaleTimeString()} UTC
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
    </div>
  );
}
