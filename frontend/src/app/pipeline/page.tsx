'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ChevronDown,
  LayoutDashboard,
  Newspaper,
  Database,
  Layers,
  Activity,
  CheckCircle,
  AlertCircle,
  XCircle,
  RefreshCw,
  TrendingUp,
  BarChart3,
  Cpu,
  HardDrive,
  Zap,
  Clock,
  ChevronRight,
  Play,
  Loader2,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/news', label: 'News & Sentiment', icon: Newspaper },
  { href: '/levels', label: 'Support & Resistance', icon: Layers },
  { href: '/pipeline', label: 'Data Pipeline', icon: Database },
];

// Types
interface HealthStatus {
  status: string;
  agent?: string;
  version?: string;
  tickers?: string[];
  timeframes?: string[];
  collectors?: Record<string, { status: string; warning?: string }>;
  storage?: { status: string; tickers: number; total_files: number };
  indicators_count?: number;
  categories?: string[];
}

interface FeatureData {
  success: boolean;
  symbol: string;
  timeframe: string;
  feature_count: number;
  features: Record<string, number | null>;
  error?: string;
}

interface QualityData {
  symbol: string;
  timeframe: string;
  status: string;
  quality_score: number;
  total_bars: number;
  date_range?: { start: string; end: string };
  issues?: string[];
}

interface StoredData {
  tickers: number;
  data: Record<string, Record<string, { rows: number; start: string; end: string }>>;
}

// Status Badge Component
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; icon: typeof CheckCircle; text: string }> = {
    healthy: { color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: CheckCircle, text: 'Healthy' },
    degraded: { color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: AlertCircle, text: 'Degraded' },
    unhealthy: { color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: XCircle, text: 'Unhealthy' },
    not_initialized: { color: 'bg-gray-500/20 text-gray-400 border-gray-500/30', icon: Clock, text: 'Not Init' },
    unavailable: { color: 'bg-gray-500/20 text-gray-400 border-gray-500/30', icon: XCircle, text: 'Unavailable' },
  };
  
  const { color, icon: Icon, text } = config[status] || config.unavailable;
  
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${color}`}>
      <Icon className="w-3 h-3" />
      {text}
    </span>
  );
}

// Card Component
function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-gray-900/50 border border-gray-800 rounded-xl backdrop-blur-sm ${className}`}>
      {children}
    </div>
  );
}

// Feature Category Component
function FeatureCategory({ 
  title, 
  features, 
  icon: Icon,
  color 
}: { 
  title: string; 
  features: Record<string, number | null>;
  icon: typeof TrendingUp;
  color: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const entries = Object.entries(features);
  const displayEntries = expanded ? entries : entries.slice(0, 4);
  
  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800/50 hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
            <Icon className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-white">{title}</span>
          <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
            {entries.length} indicators
          </span>
        </div>
        <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>
      <div className="px-4 py-3 grid grid-cols-2 gap-2">
        {displayEntries.map(([key, value]) => (
          <div key={key} className="flex items-center justify-between py-1.5 px-3 bg-gray-800/30 rounded-lg">
            <span className="text-xs text-gray-400 font-mono">{key}</span>
            <span className={`text-sm font-semibold ${
              value === null ? 'text-gray-500' : 
              (value as number) > 0 ? 'text-emerald-400' : 
              (value as number) < 0 ? 'text-red-400' : 'text-white'
            }`}>
              {value === null ? 'N/A' : typeof value === 'number' ? value.toFixed(2) : value}
            </span>
          </div>
        ))}
      </div>
      {entries.length > 4 && !expanded && (
        <div className="px-4 pb-3">
          <button 
            onClick={() => setExpanded(true)}
            className="text-xs text-primary-400 hover:text-primary-300"
          >
            + {entries.length - 4} more
          </button>
        </div>
      )}
    </div>
  );
}

export default function PipelinePage() {
  const [navOpen, setNavOpen] = useState(false);
  const [dataHealth, setDataHealth] = useState<HealthStatus | null>(null);
  const [featureHealth, setFeatureHealth] = useState<HealthStatus | null>(null);
  const [features, setFeatures] = useState<FeatureData | null>(null);
  const [quality, setQuality] = useState<QualityData | null>(null);
  const [storedData, setStoredData] = useState<StoredData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [backfilling, setBackfilling] = useState(false);
  const [backfillResult, setBackfillResult] = useState<any>(null);

  const fetchData = async () => {
    setRefreshing(true);
    try {
      // Fetch health statuses
      const [dataHealthRes, featureHealthRes, storedRes] = await Promise.all([
        fetch(`${API_BASE}/data/health`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/features/health`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/data/stored`).then(r => r.json()).catch(() => null),
      ]);
      
      setDataHealth(dataHealthRes);
      setFeatureHealth(featureHealthRes);
      setStoredData(storedRes);
      
      // Fetch features for selected ticker
      if (selectedTicker) {
        const [featuresRes, qualityRes] = await Promise.all([
          fetch(`${API_BASE}/features/latest/${selectedTicker}?timeframe=1d&bars=100`)
            .then(r => r.json()).catch(() => null),
          fetch(`${API_BASE}/data/quality/${selectedTicker}?timeframe=1d`)
            .then(r => r.json()).catch(() => null),
        ]);
        setFeatures(featuresRes);
        setQuality(qualityRes);
      }
    } catch (error) {
      console.error('Error fetching pipeline data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [selectedTicker]);

  const handleBackfill = async () => {
    setBackfilling(true);
    setBackfillResult(null);
    try {
      const response = await fetch(`${API_BASE}/data/backfill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tickers: ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'SPY'],
          years: 2,
          timeframes: ['1d']
        })
      });
      const result = await response.json();
      setBackfillResult(result);
      fetchData(); // Refresh data after backfill
    } catch (error) {
      setBackfillResult({ error: 'Backfill failed' });
    } finally {
      setBackfilling(false);
    }
  };

  // Categorize features
  const categorizeFeatures = (features: Record<string, number | null>) => {
    const categories: Record<string, Record<string, number | null>> = {
      trend: {},
      momentum: {},
      volatility: {},
      volume: {},
      price: {},
      time: {},
    };

    Object.entries(features).forEach(([key, value]) => {
      if (key.includes('sma') || key.includes('ema') || key.includes('adx') || key.includes('di')) {
        categories.trend[key] = value;
      } else if (key.includes('rsi') || key.includes('macd') || key.includes('stoch') || key.includes('cci') || key.includes('williams')) {
        categories.momentum[key] = value;
      } else if (key.includes('atr') || key.includes('bb_') || key.includes('volatility') || key.includes('range')) {
        categories.volatility[key] = value;
      } else if (key.includes('volume') || key.includes('obv') || key.includes('vwap') || key.includes('rvol')) {
        categories.volume[key] = value;
      } else if (key.includes('return') || key.includes('move') || key.includes('pos_') || key.includes('bar_') || key.includes('velocity') || key.includes('accel')) {
        categories.price[key] = value;
      } else if (key.includes('hour') || key.includes('minute') || key.includes('session') || key.includes('day_') || key.includes('is_')) {
        categories.time[key] = value;
      } else if (['open', 'high', 'low', 'close'].includes(key)) {
        categories.price[key] = value;
      }
    });

    return categories;
  };

  const tickers = storedData?.data ? Object.keys(storedData.data) : ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'SPY'];

  if (loading) {
    return (
      <div className="h-screen w-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading pipeline data...</p>
        </div>
      </div>
    );
  }

  const featureCategories = features?.features ? categorizeFeatures(features.features) : null;

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-3 sticky top-0 z-30">
        <div className="flex items-center justify-between gap-4 max-w-7xl mx-auto">
          {/* Navigation Dropdown */}
          <div className="relative">
            <button
              onClick={() => setNavOpen(!navOpen)}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg transition-colors"
            >
              <Database className="w-4 h-4 text-primary-500" />
              <span className="text-sm font-semibold text-white">Data Pipeline</span>
              <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${navOpen ? 'rotate-180' : ''}`} />
            </button>
            {navOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setNavOpen(false)} />
                <div className="absolute left-0 z-20 mt-1 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-xl overflow-hidden">
                  {navItems.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setNavOpen(false)}
                      className={`flex items-center gap-3 px-4 py-2.5 hover:bg-gray-700 transition-colors ${
                        item.href === '/pipeline' ? 'bg-primary-600/20 border-l-2 border-primary-500' : ''
                      }`}
                    >
                      <item.icon className={`w-4 h-4 ${item.href === '/pipeline' ? 'text-primary-400' : 'text-gray-400'}`} />
                      <span className={`text-sm font-medium ${item.href === '/pipeline' ? 'text-white' : 'text-gray-300'}`}>
                        {item.label}
                      </span>
                    </Link>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* TICK Branding */}
          <div className="hidden md:block text-center flex-1">
            <h1 className="text-lg font-bold text-white">M1 Data Pipeline</h1>
            <p className="text-xs text-gray-400">Foundation & Data Infrastructure</p>
          </div>

          {/* Refresh Button */}
          <button
            onClick={fetchData}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 text-gray-400 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm text-gray-300 hidden sm:inline">Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-4 space-y-6">
        {/* Health Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Data Agent Card */}
          <Card className="p-4">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <Database className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">Data Agent</h3>
                  <p className="text-xs text-gray-400">v{dataHealth?.version || '1.0.0'}</p>
                </div>
              </div>
              <StatusBadge status={dataHealth?.status || 'unavailable'} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Collectors</span>
                <span className="text-white">
                  {dataHealth?.collectors ? Object.keys(dataHealth.collectors).length : 0} active
                </span>
              </div>
              {dataHealth?.collectors && Object.entries(dataHealth.collectors).map(([name, info]) => (
                <div key={name} className="flex items-center justify-between pl-4 text-xs">
                  <span className="text-gray-500">{name}</span>
                  <StatusBadge status={info.status} />
                </div>
              ))}
            </div>
          </Card>

          {/* Feature Agent Card */}
          <Card className="p-4">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">Feature Agent</h3>
                  <p className="text-xs text-gray-400">v{featureHealth?.version || '1.0.0'}</p>
                </div>
              </div>
              <StatusBadge status={featureHealth?.status || 'unavailable'} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Indicators</span>
                <span className="text-white">{featureHealth?.indicators_count || 0}+</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Categories</span>
                <span className="text-white">6 (Trend, Momentum, Vol...)</span>
              </div>
            </div>
          </Card>

          {/* Storage Card */}
          <Card className="p-4">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <HardDrive className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">Storage</h3>
                  <p className="text-xs text-gray-400">Parquet Files</p>
                </div>
              </div>
              <StatusBadge status={dataHealth?.storage?.status || 'unavailable'} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Tickers</span>
                <span className="text-white">{storedData?.tickers || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Total Files</span>
                <span className="text-white">{dataHealth?.storage?.total_files || 0}</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Backfill Section */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Zap className="w-5 h-5 text-amber-400" />
              <h3 className="font-semibold text-white">Data Backfill</h3>
            </div>
            <button
              onClick={handleBackfill}
              disabled={backfilling}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 rounded-lg transition-colors"
            >
              {backfilling ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span className="text-sm font-medium">
                {backfilling ? 'Backfilling...' : 'Run Backfill (2yr)'}
              </span>
            </button>
          </div>
          
          {backfillResult && (
            <div className={`p-3 rounded-lg ${backfillResult.error ? 'bg-red-500/10 border border-red-500/30' : 'bg-emerald-500/10 border border-emerald-500/30'}`}>
              {backfillResult.error ? (
                <p className="text-red-400 text-sm">{backfillResult.error}</p>
              ) : (
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-emerald-400">{backfillResult.tickers}</p>
                    <p className="text-xs text-gray-400">Tickers</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-emerald-400">{backfillResult.successful}</p>
                    <p className="text-xs text-gray-400">Successful</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-emerald-400">{backfillResult.total_rows?.toLocaleString()}</p>
                    <p className="text-xs text-gray-400">Total Rows</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-emerald-400">{backfillResult.timeframes?.length}</p>
                    <p className="text-xs text-gray-400">Timeframes</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Stored Data Table */}
          {storedData?.data && Object.keys(storedData.data).length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left py-2 px-3 text-gray-400 font-medium">Ticker</th>
                    <th className="text-left py-2 px-3 text-gray-400 font-medium">Timeframe</th>
                    <th className="text-right py-2 px-3 text-gray-400 font-medium">Rows</th>
                    <th className="text-left py-2 px-3 text-gray-400 font-medium">Date Range</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(storedData.data).map(([ticker, timeframes]) =>
                    Object.entries(timeframes).map(([tf, info], idx) => (
                      <tr key={`${ticker}-${tf}`} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                        <td className="py-2 px-3 font-semibold text-white">{idx === 0 ? ticker : ''}</td>
                        <td className="py-2 px-3 text-gray-300">{tf}</td>
                        <td className="py-2 px-3 text-right text-white">{info.rows.toLocaleString()}</td>
                        <td className="py-2 px-3 text-gray-400 text-xs">
                          {new Date(info.start).toLocaleDateString()} → {new Date(info.end).toLocaleDateString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Feature Explorer */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-5 h-5 text-primary-400" />
              <h3 className="font-semibold text-white">Feature Explorer</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Ticker:</span>
              <select
                value={selectedTicker}
                onChange={(e) => setSelectedTicker(e.target.value)}
                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
              >
                {tickers.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Data Quality */}
          {quality && (
            <div className="mb-6 p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Data Quality for {quality.symbol}</span>
                <StatusBadge status={quality.status} />
              </div>
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-white">{quality.quality_score ?? 0}%</p>
                  <p className="text-xs text-gray-400">Quality Score</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{(quality.total_bars ?? 0).toLocaleString()}</p>
                  <p className="text-xs text-gray-400">Total Bars</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{quality.date_range?.start?.slice(0, 10) ?? 'N/A'}</p>
                  <p className="text-xs text-gray-400">Start Date</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{quality.date_range?.end?.slice(0, 10) ?? 'N/A'}</p>
                  <p className="text-xs text-gray-400">End Date</p>
                </div>
              </div>
              {quality.issues && quality.issues.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {quality.issues.map((issue, idx) => (
                    <span key={idx} className="text-xs px-2 py-1 bg-amber-500/20 text-amber-400 rounded">
                      {issue}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Features Grid */}
          {features?.success && featureCategories ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FeatureCategory 
                title="Trend Indicators" 
                features={featureCategories.trend}
                icon={TrendingUp}
                color="bg-blue-500"
              />
              <FeatureCategory 
                title="Momentum Indicators" 
                features={featureCategories.momentum}
                icon={Activity}
                color="bg-purple-500"
              />
              <FeatureCategory 
                title="Volatility Indicators" 
                features={featureCategories.volatility}
                icon={BarChart3}
                color="bg-amber-500"
              />
              <FeatureCategory 
                title="Volume Indicators" 
                features={featureCategories.volume}
                icon={Database}
                color="bg-emerald-500"
              />
              <FeatureCategory 
                title="Price Features" 
                features={featureCategories.price}
                icon={Zap}
                color="bg-red-500"
              />
              <FeatureCategory 
                title="Time Features" 
                features={featureCategories.time}
                icon={Clock}
                color="bg-cyan-500"
              />
            </div>
          ) : features?.error ? (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-amber-400 mx-auto mb-3" />
              <p className="text-gray-400">{features.error}</p>
              <p className="text-sm text-gray-500 mt-2">Run backfill first to load historical data</p>
            </div>
          ) : (
            <div className="text-center py-8">
              <Loader2 className="w-8 h-8 text-gray-400 mx-auto mb-3 animate-spin" />
              <p className="text-gray-400">Loading features...</p>
            </div>
          )}

          {features?.success && (
            <div className="mt-4 pt-4 border-t border-gray-800 flex items-center justify-between">
              <span className="text-sm text-gray-400">
                Total Features: <span className="text-white font-semibold">{features.feature_count}</span>
              </span>
              <span className="text-xs text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            </div>
          )}
        </Card>
      </main>
    </div>
  );
}




