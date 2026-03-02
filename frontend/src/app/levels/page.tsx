'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Layers,
  ChevronDown,
  Loader2,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  Clock,
  BarChart3,
  Zap
} from 'lucide-react';
import { SP500_STOCKS } from '@/lib/mockData';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
interface PriceLevel {
  price: number;
  strength: number;
  type: 'support' | 'resistance';
  touches: number;
  validated: boolean;
  validation_rate: number;
  breakout_probability: number;
  first_touch: string | null;
  last_touch: string | null;
  volume: number;
  volume_percentile: number;
  has_volume_confirmation: boolean;
}

interface LevelsResponse {
  status?: string;
  symbol: string;
  timestamp: string;
  current_price: number;
  timeframe: string;
  support_levels: PriceLevel[];
  resistance_levels: PriceLevel[];
  total_levels: number;
  nearest_support: number | null;
  nearest_resistance: number | null;
  message?: string;
  metadata?: {
    peaks_detected: number;
    valleys_detected: number;
    data_points: number;
    lookback_days: number;
    data_source: string;
  };
  api_metadata?: {
    processing_time_seconds: number;
  };
}

export default function LevelsPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [minStrength, setMinStrength] = useState(30);
  const [maxLevels, setMaxLevels] = useState(5);
  const [timeframe, setTimeframe] = useState('1d');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [levelsData, setLevelsData] = useState<LevelsResponse | null>(null);

  const timeframes = [
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' },
    { value: '1w', label: '1 Week' },
    { value: '1mo', label: '1 Month' },
  ];

  const handleDetectLevels = async () => {
    setLoading(true);
    setError(null);
    setLevelsData(null);

    try {
      const url = `${API_BASE_URL}/api/v1/levels/${selectedSymbol}?min_strength=${minStrength}&max_levels=${maxLevels}&timeframe=${timeframe}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: LevelsResponse = await response.json();

      if (data.status === 'error') {
        setError((data as any).message || 'An error occurred while detecting levels');
      } else {
        setLevelsData(data);
      }
    } catch (err) {
      setError(`Failed to connect to backend: ${err instanceof Error ? err.message : 'Unknown error'}. Make sure the backend is running on ${API_BASE_URL}`);
    } finally {
      setLoading(false);
    }
  };

  const getStrengthColor = (strength: number) => {
    if (strength >= 80) return 'text-success-400';
    if (strength >= 60) return 'text-emerald-400';
    if (strength >= 40) return 'text-amber-400';
    if (strength >= 20) return 'text-orange-400';
    return 'text-danger-400';
  };

  const getStrengthBgColor = (strength: number) => {
    if (strength >= 80) return 'bg-success-500';
    if (strength >= 60) return 'bg-emerald-500';
    if (strength >= 40) return 'bg-amber-500';
    if (strength >= 20) return 'bg-orange-500';
    return 'bg-danger-500';
  };

  const getStrengthLabel = (strength: number) => {
    if (strength >= 80) return 'Very Strong';
    if (strength >= 60) return 'Strong';
    if (strength >= 40) return 'Moderate';
    if (strength >= 20) return 'Weak';
    return 'Very Weak';
  };

  return (
    <div className="min-h-screen w-full bg-gray-950 overflow-y-auto overflow-x-hidden">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-2 sticky top-0 z-50">
        <div className="flex items-center justify-between gap-4 max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-sm">Dashboard</span>
            </Link>
            <div className="h-4 w-px bg-gray-700" />
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-primary-500" />
              <h1 className="text-lg font-bold text-white">Support & Resistance</h1>
            </div>
          </div>
          <div className="flex-shrink-0">
            <p className="text-xs text-gray-400 hidden sm:block">TICK - Level Detection Agent</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full p-4 md:p-6 pb-12">
        {/* Input Section */}
        <div className="max-w-[1800px] mx-auto mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 md:p-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Level Detection Configuration
            </h2>
            <div className="flex flex-wrap items-end gap-4">
              {/* Stock Selector */}
              <div className="relative flex-1 min-w-[200px]">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Stock Ticker
                </label>
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-750 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                >
                  <div className="text-left">
                    <span className="text-white font-semibold">{selectedSymbol}</span>
                    <span className="text-gray-400 text-sm ml-2">
                      {SP500_STOCKS.find(s => s.symbol === selectedSymbol)?.name || ''}
                    </span>
                  </div>
                  <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                </button>
                {isDropdownOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setIsDropdownOpen(false)}
                    />
                    <div className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-80 overflow-auto">
                      {['Technology', 'Energy', 'Healthcare', 'Finance', 'Consumer'].map((sector) => (
                        <div key={sector}>
                          <div className="px-4 py-1.5 bg-gray-900 text-xs font-semibold text-gray-500 uppercase tracking-wider sticky top-0">
                            {sector}
                          </div>
                          {SP500_STOCKS.filter((s: any) => s.sector === sector).map((stock) => (
                            <button
                              key={stock.symbol}
                              onClick={() => {
                                setSelectedSymbol(stock.symbol);
                                setIsDropdownOpen(false);
                              }}
                              className={`w-full px-4 py-2 text-left hover:bg-gray-700 transition-colors ${
                                selectedSymbol === stock.symbol ? 'bg-primary-600/20' : ''
                              }`}
                            >
                              <div className="font-semibold text-white">{stock.symbol}</div>
                              <div className="text-xs text-gray-400">{stock.name}</div>
                            </button>
                          ))}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>

              {/* Timeframe */}
              <div className="w-32">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Timeframe
                </label>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                >
                  {timeframes.map((tf) => (
                    <option key={tf.value} value={tf.value}>
                      {tf.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Min Strength */}
              <div className="w-32">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Min Strength
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={minStrength}
                  onChange={(e) => setMinStrength(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                />
              </div>

              {/* Max Levels */}
              <div className="w-32">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Max Levels
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={maxLevels}
                  onChange={(e) => setMaxLevels(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                />
              </div>

              {/* Detect Button */}
              <button
                onClick={handleDetectLevels}
                disabled={loading}
                className="px-6 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-primary-600/50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Detecting...
                  </>
                ) : (
                  <>
                    <Target className="w-4 h-4" />
                    Detect Levels
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="max-w-[1800px] mx-auto">
          {/* Error Message */}
          {error && (
            <div className="bg-danger-500/10 border border-danger-500/50 rounded-xl p-4 flex items-start gap-3 mb-6">
              <AlertCircle className="w-5 h-5 text-danger-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-danger-400 font-semibold">Error</h3>
                <p className="text-danger-300 text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
              <p className="text-gray-400">Detecting support and resistance levels...</p>
            </div>
          )}

          {/* Results */}
          {levelsData && !loading && (
            <div className="space-y-6">
              {/* Overview Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                {/* Current Price */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
                    <Activity className="w-4 h-4" />
                    Current Price
                  </div>
                  <div className="text-2xl font-bold text-white">
                    ${levelsData.current_price.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">{levelsData.symbol}</div>
                </div>

                {/* Nearest Support */}
                <div className="bg-gray-900 border border-success-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-success-400 text-xs font-medium mb-2">
                    <TrendingDown className="w-4 h-4" />
                    Nearest Support
                  </div>
                  <div className="text-2xl font-bold text-success-400">
                    {levelsData.nearest_support ? `$${levelsData.nearest_support.toFixed(2)}` : 'N/A'}
                  </div>
                  {levelsData.nearest_support && (
                    <div className="text-xs text-gray-400 mt-1">
                      {((levelsData.current_price - levelsData.nearest_support) / levelsData.current_price * 100).toFixed(2)}% below
                    </div>
                  )}
                </div>

                {/* Nearest Resistance */}
                <div className="bg-gray-900 border border-danger-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-danger-400 text-xs font-medium mb-2">
                    <TrendingUp className="w-4 h-4" />
                    Nearest Resistance
                  </div>
                  <div className="text-2xl font-bold text-danger-400">
                    {levelsData.nearest_resistance ? `$${levelsData.nearest_resistance.toFixed(2)}` : 'N/A'}
                  </div>
                  {levelsData.nearest_resistance && (
                    <div className="text-xs text-gray-400 mt-1">
                      {((levelsData.nearest_resistance - levelsData.current_price) / levelsData.current_price * 100).toFixed(2)}% above
                    </div>
                  )}
                </div>

                {/* Processing Info */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
                    <Clock className="w-4 h-4" />
                    Processing
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {levelsData.api_metadata?.processing_time_seconds.toFixed(2)}s
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {levelsData.total_levels} levels detected
                  </div>
                </div>
              </div>

              {/* Support & Resistance Levels */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Support Levels */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                  <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-success-400 uppercase tracking-wider flex items-center gap-2">
                      <TrendingDown className="w-4 h-4" />
                      Support Levels
                    </h3>
                    <span className="text-xs text-gray-500">{levelsData.support_levels.length} levels</span>
                  </div>
                  <div className="divide-y divide-gray-800">
                    {levelsData.support_levels.length === 0 ? (
                      <div className="p-8 text-center text-gray-400">
                        No support levels detected
                      </div>
                    ) : (
                      levelsData.support_levels.map((level, index) => (
                        <LevelCard key={index} level={level} type="support" currentPrice={levelsData.current_price} />
                      ))
                    )}
                  </div>
                </div>

                {/* Resistance Levels */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                  <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-danger-400 uppercase tracking-wider flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Resistance Levels
                    </h3>
                    <span className="text-xs text-gray-500">{levelsData.resistance_levels.length} levels</span>
                  </div>
                  <div className="divide-y divide-gray-800">
                    {levelsData.resistance_levels.length === 0 ? (
                      <div className="p-8 text-center text-gray-400">
                        No resistance levels detected
                      </div>
                    ) : (
                      levelsData.resistance_levels.map((level, index) => (
                        <LevelCard key={index} level={level} type="resistance" currentPrice={levelsData.current_price} />
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Metadata */}
              {levelsData.metadata && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4" />
                    Detection Metadata
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 sm:gap-4">
                    <MetricCard label="Peaks Detected" value={levelsData.metadata.peaks_detected} />
                    <MetricCard label="Valleys Detected" value={levelsData.metadata.valleys_detected} />
                    <MetricCard label="Data Points" value={levelsData.metadata.data_points} />
                    <MetricCard label="Lookback Days" value={levelsData.metadata.lookback_days} />
                    <MetricCard label="Data Source" value={levelsData.metadata.data_source} />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Empty State */}
          {!levelsData && !loading && !error && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center justify-center text-center">
              <Layers className="w-16 h-16 text-gray-700 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Ready to Detect Levels</h3>
              <p className="text-gray-400 max-w-md">
                Select a stock ticker, configure the parameters, and click "Detect Levels" to identify key support and resistance price levels.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Level Card Component
function LevelCard({
  level,
  type,
  currentPrice
}: {
  level: PriceLevel;
  type: 'support' | 'resistance';
  currentPrice: number;
}) {
  const distance = type === 'support'
    ? ((currentPrice - level.price) / currentPrice * 100)
    : ((level.price - currentPrice) / currentPrice * 100);

  const getStrengthColor = (strength: number) => {
    if (strength >= 80) return 'text-success-400';
    if (strength >= 60) return 'text-emerald-400';
    if (strength >= 40) return 'text-amber-400';
    if (strength >= 20) return 'text-orange-400';
    return 'text-danger-400';
  };

  const getStrengthBgColor = (strength: number) => {
    if (strength >= 80) return 'bg-success-500';
    if (strength >= 60) return 'bg-emerald-500';
    if (strength >= 40) return 'bg-amber-500';
    if (strength >= 20) return 'bg-orange-500';
    return 'bg-danger-500';
  };

  return (
    <div className="p-4 hover:bg-gray-800/50 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className={`text-lg font-bold ${type === 'support' ? 'text-success-400' : 'text-danger-400'}`}>
            ${level.price.toFixed(2)}
          </div>
          <div className="text-xs text-gray-400">
            {distance.toFixed(2)}% {type === 'support' ? 'below' : 'above'} current
          </div>
        </div>
        <div className="text-right">
          <div className={`text-sm font-bold ${getStrengthColor(level.strength)}`}>
            {level.strength}%
          </div>
          <div className="text-xs text-gray-500">Strength</div>
        </div>
      </div>

      {/* Strength Bar */}
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full ${getStrengthBgColor(level.strength)} transition-all duration-300`}
          style={{ width: `${level.strength}%` }}
        />
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 sm:gap-2 text-xs">
        <div>
          <span className="text-gray-500">Touches:</span>
          <span className="text-white ml-1">{level.touches}</span>
        </div>
        <div>
          <span className="text-gray-500">Breakout:</span>
          <span className="text-amber-400 ml-1">{level.breakout_probability.toFixed(1)}%</span>
        </div>
        <div>
          <span className="text-gray-500">Volume:</span>
          <span className={`ml-1 ${level.has_volume_confirmation ? 'text-success-400' : 'text-gray-400'}`}>
            {level.has_volume_confirmation ? 'Confirmed' : 'No'}
          </span>
        </div>
      </div>
    </div>
  );
}

// Metric Card Component
function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-sm font-semibold text-white">{value}</div>
    </div>
  );
}
