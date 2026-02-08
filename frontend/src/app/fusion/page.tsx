'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Zap,
  ChevronDown,
  Loader2,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Brain,
  BarChart3,
  Activity,
  Clock,
  CheckCircle2,
  Info,
  RefreshCw,
} from 'lucide-react';
import { SP500_STOCKS } from '@/lib/mockData';
import { apiClient, FusionSignalResponse } from '@/lib/api/client';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function FusionPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fusionData, setFusionData] = useState<FusionSignalResponse | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const handleGetSignal = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getQuickFusionSignal(selectedSymbol);
      setFusionData(data);
    } catch (err) {
      setError(`Failed to get trading signal: ${err instanceof Error ? err.message : 'Unknown error'}. Make sure the backend is running on ${API_BASE_URL}`);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    if (autoRefresh && !loading) {
      const interval = setInterval(handleGetSignal, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedSymbol, loading]);

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return <TrendingUp className="w-8 h-8" />;
      case 'SELL':
        return <TrendingDown className="w-8 h-8" />;
      default:
        return <Minus className="w-8 h-8" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return {
          text: 'text-success-400',
          bg: 'bg-success-500/20',
          border: 'border-success-500/50',
        };
      case 'SELL':
        return {
          text: 'text-danger-400',
          bg: 'bg-danger-500/20',
          border: 'border-danger-500/50',
        };
      default:
        return {
          text: 'text-gray-400',
          bg: 'bg-gray-500/20',
          border: 'border-gray-500/50',
        };
    }
  };

  const getScoreColor = (score: number) => {
    if (score > 0.3) return 'text-success-400';
    if (score < -0.3) return 'text-danger-400';
    return 'text-gray-400';
  };

  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 0.8) return { label: 'Very High', color: 'text-success-400' };
    if (confidence >= 0.6) return { label: 'High', color: 'text-emerald-400' };
    if (confidence >= 0.4) return { label: 'Medium', color: 'text-amber-400' };
    if (confidence >= 0.2) return { label: 'Low', color: 'text-orange-400' };
    return { label: 'Very Low', color: 'text-danger-400' };
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
              <Zap className="w-5 h-5 text-primary-500" />
              <h1 className="text-lg font-bold text-white">Trading Signals</h1>
            </div>
          </div>
          <div className="flex-shrink-0">
            <p className="text-xs text-gray-400 hidden sm:block">TICK - Fusion Agent</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full p-4 md:p-6 pb-12">
        {/* Input Section */}
        <div className="max-w-[1400px] mx-auto mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 md:p-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Signal Configuration
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
                    <div className="fixed inset-0 z-10" onClick={() => setIsDropdownOpen(false)} />
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

              {/* Auto Refresh Toggle */}
              <div className="flex items-center gap-2">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  <span className="ml-2 text-sm text-gray-400">Auto-refresh</span>
                </label>
              </div>

              {/* Get Signal Button */}
              <button
                onClick={handleGetSignal}
                disabled={loading}
                className="px-6 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-primary-600/50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Get Trading Signal
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="max-w-[1400px] mx-auto">
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
              <p className="text-gray-400">Generating trading signal...</p>
              <p className="text-gray-500 text-sm mt-2">Analyzing price, trend, support/resistance, and sentiment</p>
            </div>
          )}

          {/* Signal Results */}
          {fusionData && !loading && (
            <div className="space-y-6">
              {/* Main Signal Card */}
              <div className={`bg-gray-900 border ${getSignalColor(fusionData.signal).border} rounded-xl overflow-hidden`}>
                <div className={`${getSignalColor(fusionData.signal).bg} p-6`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-16 h-16 rounded-xl ${getSignalColor(fusionData.signal).bg} border ${getSignalColor(fusionData.signal).border} flex items-center justify-center ${getSignalColor(fusionData.signal).text}`}>
                        {getSignalIcon(fusionData.signal)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-gray-400 uppercase tracking-wider">Trading Signal</span>
                          {autoRefresh && (
                            <span className="flex items-center gap-1 text-xs text-primary-400">
                              <RefreshCw className="w-3 h-3" />
                              Auto
                            </span>
                          )}
                        </div>
                        <div className={`text-4xl font-bold ${getSignalColor(fusionData.signal).text}`}>
                          {fusionData.signal}
                        </div>
                        <div className="text-gray-400 text-sm mt-1">
                          {fusionData.symbol} - {new Date(fusionData.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-400 mb-1">Confidence</div>
                      <div className={`text-3xl font-bold ${getConfidenceLevel(fusionData.confidence).color}`}>
                        {(fusionData.confidence * 100).toFixed(1)}%
                      </div>
                      <div className={`text-sm ${getConfidenceLevel(fusionData.confidence).color}`}>
                        {getConfidenceLevel(fusionData.confidence).label}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Fused Score */}
                <div className="p-6 border-t border-gray-800">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-gray-400">Fused Score</span>
                    <span className={`text-lg font-bold ${getScoreColor(fusionData.fused_score)}`}>
                      {fusionData.fused_score.toFixed(3)}
                    </span>
                  </div>
                  <div className="h-3 bg-gray-800 rounded-full overflow-hidden relative">
                    <div className="absolute inset-0 flex">
                      <div className="w-1/2 bg-gradient-to-r from-danger-500 to-gray-700"></div>
                      <div className="w-1/2 bg-gradient-to-r from-gray-700 to-success-500"></div>
                    </div>
                    <div
                      className="absolute top-0 bottom-0 w-1 bg-white shadow-lg"
                      style={{ left: `${(fusionData.fused_score + 1) * 50}%`, transform: 'translateX(-50%)' }}
                    />
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-gray-500">
                    <span>-1 (Bearish)</span>
                    <span>0 (Neutral)</span>
                    <span>+1 (Bullish)</span>
                  </div>
                </div>
              </div>

              {/* Component Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Price Forecast */}
                <ComponentCard
                  title="Price Forecast"
                  icon={<Activity className="w-5 h-5" />}
                  data={fusionData.components.price_forecast}
                  weight={fusionData.components.price_forecast?.weight ?? fusionData.weights?.price_forecast ?? 0.3}
                />

                {/* Trend Classification */}
                <ComponentCard
                  title="Trend Classification"
                  icon={<BarChart3 className="w-5 h-5" />}
                  data={fusionData.components.trend_classification}
                  weight={fusionData.components.trend_classification?.weight ?? fusionData.weights?.trend_classification ?? 0.25}
                />

                {/* Support/Resistance */}
                <ComponentCard
                  title="Support/Resistance"
                  icon={<Target className="w-5 h-5" />}
                  data={fusionData.components.support_resistance}
                  weight={fusionData.components.support_resistance?.weight ?? fusionData.weights?.support_resistance ?? 0.2}
                />

                {/* Sentiment */}
                <ComponentCard
                  title="Sentiment"
                  icon={<Brain className="w-5 h-5" />}
                  data={fusionData.components.sentiment}
                  weight={fusionData.components.sentiment?.weight ?? fusionData.weights?.sentiment ?? 0.25}
                />
              </div>

              {/* Reasoning */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  Signal Reasoning
                </h3>
                <p className="text-white">{fusionData.reasoning}</p>
              </div>

              {/* Rules Applied */}
              {fusionData.rules_applied && fusionData.rules_applied.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Rules Applied ({fusionData.rules_applied.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {fusionData.rules_applied.map((rule, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-primary-500/20 text-primary-400 rounded-full text-sm"
                      >
                        {rule}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Empty State */}
          {!fusionData && !loading && !error && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center justify-center text-center">
              <Zap className="w-16 h-16 text-gray-700 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Ready to Generate Signal</h3>
              <p className="text-gray-400 max-w-md">
                Select a stock ticker and click "Get Trading Signal" to generate a fused trading recommendation
                based on price forecast, trend classification, support/resistance levels, and sentiment analysis.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Component Card
function ComponentCard({
  title,
  icon,
  data,
  weight,
}: {
  title: string;
  icon: React.ReactNode;
  data?: {
    signal: string;
    score: number;
    confidence: number;
    predicted_price?: number;
  };
  weight?: number;
}) {
  const getSignalColor = (signal?: string) => {
    if (!signal) return 'text-gray-400';
    switch (signal.toUpperCase()) {
      case 'BUY':
      case 'BULLISH':
        return 'text-success-400';
      case 'SELL':
      case 'BEARISH':
        return 'text-danger-400';
      default:
        return 'text-gray-400';
    }
  };

  const getScoreColor = (score?: number) => {
    if (score === undefined) return 'text-gray-400';
    if (score > 0.3) return 'text-success-400';
    if (score < -0.3) return 'text-danger-400';
    return 'text-amber-400';
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-gray-400">
          {icon}
          <span className="text-sm font-medium">{title}</span>
        </div>
        {weight !== undefined && (
          <span className="text-xs text-gray-500">{(weight * 100).toFixed(0)}% weight</span>
        )}
      </div>

      {data ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Status</span>
            <span className={`font-bold ${getSignalColor(data.signal || data.status || 'N/A')}`}>
              {data.signal || data.status || 'N/A'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Score</span>
            <span className={`font-semibold ${getScoreColor(data.score ?? data.signal_value ?? 0)}`}>
              {(data.score ?? data.signal_value ?? 0).toFixed(3)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Confidence</span>
            <span className="text-white font-semibold">
              {((data.confidence ?? 0) * 100).toFixed(1)}%
            </span>
          </div>
          {(data.predicted_price || data.contribution !== undefined) && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">{data.predicted_price ? 'Predicted' : 'Contribution'}</span>
              <span className="text-primary-400 font-semibold">
                {data.predicted_price ? `$${data.predicted_price.toFixed(2)}` : (data.contribution ?? 0).toFixed(3)}
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-gray-500 text-sm">No data</p>
        </div>
      )}
    </div>
  );
}
