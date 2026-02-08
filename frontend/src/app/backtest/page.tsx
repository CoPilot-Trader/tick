'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  LineChart,
  ChevronDown,
  Loader2,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Percent,
  BarChart3,
  Clock,
  Target,
  Activity,
  Award,
  AlertTriangle,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { SP500_STOCKS } from '@/lib/mockData';
import { apiClient, BacktestResult, BacktestTrade } from '@/lib/api/client';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

export default function BacktestPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [days, setDays] = useState(180);
  const [initialCapital, setInitialCapital] = useState(100000);
  const [stopLossPct, setStopLossPct] = useState(0.05);
  const [takeProfitPct, setTakeProfitPct] = useState(0.10);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backtestData, setBacktestData] = useState<BacktestResult | null>(null);

  const handleRunBacktest = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.runBacktest({
        ticker: selectedSymbol,
        days,
        initial_capital: initialCapital,
        stop_loss_pct: stopLossPct,
        take_profit_pct: takeProfitPct,
      });
      setBacktestData(data);
    } catch (err) {
      setError(`Failed to run backtest: ${err instanceof Error ? err.message : 'Unknown error'}. Make sure the backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
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
              <LineChart className="w-5 h-5 text-primary-500" />
              <h1 className="text-lg font-bold text-white">Backtesting</h1>
            </div>
          </div>
          <div className="flex-shrink-0">
            <p className="text-xs text-gray-400 hidden sm:block">TICK - Strategy Backtester</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full p-4 md:p-6 pb-12">
        {/* Configuration */}
        <div className="max-w-[1800px] mx-auto mb-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 md:p-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Backtest Configuration
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

              {/* Days */}
              <div className="w-28">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Days
                </label>
                <input
                  type="number"
                  min="60"
                  max="730"
                  value={days}
                  onChange={(e) => setDays(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Initial Capital */}
              <div className="w-36">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Initial Capital
                </label>
                <input
                  type="number"
                  min="1000"
                  step="1000"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Stop Loss */}
              <div className="w-28">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Stop Loss %
                </label>
                <input
                  type="number"
                  min="0.01"
                  max="0.20"
                  step="0.01"
                  value={stopLossPct}
                  onChange={(e) => setStopLossPct(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Take Profit */}
              <div className="w-28">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Take Profit %
                </label>
                <input
                  type="number"
                  min="0.02"
                  max="0.50"
                  step="0.01"
                  value={takeProfitPct}
                  onChange={(e) => setTakeProfitPct(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Run Button */}
              <button
                onClick={handleRunBacktest}
                disabled={loading}
                className="px-6 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-primary-600/50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <LineChart className="w-4 h-4" />
                    Run Backtest
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="max-w-[1800px] mx-auto">
          {/* Error */}
          {error && (
            <div className="bg-danger-500/10 border border-danger-500/50 rounded-xl p-4 flex items-start gap-3 mb-6">
              <AlertCircle className="w-5 h-5 text-danger-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-danger-400 font-semibold">Error</h3>
                <p className="text-danger-300 text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
              <p className="text-gray-400">Running backtest simulation...</p>
              <p className="text-gray-500 text-sm mt-2">This may take a moment for longer periods</p>
            </div>
          )}

          {/* Results */}
          {backtestData && !loading && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <MetricCard
                  icon={<DollarSign className="w-5 h-5" />}
                  label="Final Equity"
                  value={formatCurrency(backtestData.final_equity ?? 0)}
                  subtext={formatPercent(backtestData.total_return ?? 0)}
                  positive={(backtestData.total_return ?? 0) >= 0}
                />
                <MetricCard
                  icon={<Activity className="w-5 h-5" />}
                  label="Total Trades"
                  value={(backtestData.total_trades ?? 0).toString()}
                  subtext={`${backtestData.winning_trades ?? 0}W / ${backtestData.losing_trades ?? 0}L`}
                />
                <MetricCard
                  icon={<Target className="w-5 h-5" />}
                  label="Win Rate"
                  value={`${((backtestData.win_rate ?? 0) * 100).toFixed(1)}%`}
                  positive={(backtestData.win_rate ?? 0) >= 0.5}
                />
                <MetricCard
                  icon={<BarChart3 className="w-5 h-5" />}
                  label="Profit Factor"
                  value={(backtestData.profit_factor ?? 0).toFixed(2)}
                  positive={(backtestData.profit_factor ?? 0) >= 1}
                />
                <MetricCard
                  icon={<AlertTriangle className="w-5 h-5" />}
                  label="Max Drawdown"
                  value={`${((backtestData.max_drawdown_pct ?? 0) * 100).toFixed(2)}%`}
                  subtext={formatCurrency(backtestData.max_drawdown ?? 0)}
                  positive={false}
                />
                <MetricCard
                  icon={<Award className="w-5 h-5" />}
                  label="Sharpe Ratio"
                  value={(backtestData.sharpe_ratio ?? 0).toFixed(2)}
                  subtext={`Sortino: ${(backtestData.sortino_ratio ?? 0).toFixed(2)}`}
                  positive={(backtestData.sharpe_ratio ?? 0) >= 1}
                />
              </div>

              {/* Equity Curve */}
              {backtestData.equity_curve && backtestData.equity_curve.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <LineChart className="w-4 h-4" />
                    Equity Curve
                  </h3>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsLineChart data={backtestData.equity_curve}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                          dataKey="date"
                          stroke="#9CA3AF"
                          tick={{ fill: '#9CA3AF', fontSize: 12 }}
                          tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        />
                        <YAxis
                          stroke="#9CA3AF"
                          tick={{ fill: '#9CA3AF', fontSize: 12 }}
                          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1F2937',
                            border: '1px solid #374151',
                            borderRadius: '8px',
                          }}
                          labelFormatter={(value) => new Date(value).toLocaleDateString()}
                          formatter={(value: number) => [formatCurrency(value), 'Equity']}
                        />
                        <ReferenceLine
                          y={backtestData.initial_capital ?? 100000}
                          stroke="#6B7280"
                          strokeDasharray="3 3"
                          label={{ value: 'Initial', fill: '#6B7280', fontSize: 12 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="equity"
                          stroke="#3B82F6"
                          strokeWidth={2}
                          dot={false}
                        />
                      </RechartsLineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Trade List */}
              {backtestData.trades && backtestData.trades.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                  <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Trade History
                    </h3>
                    <span className="text-xs text-gray-500">{backtestData.trades.length} trades</span>
                  </div>
                  <div className="max-h-96 overflow-auto">
                    <table className="w-full">
                      <thead className="bg-gray-800 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-400">Entry Date</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-400">Exit Date</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-400">Side</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold text-gray-400">Entry Price</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold text-gray-400">Exit Price</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold text-gray-400">P&L</th>
                          <th className="px-4 py-2 text-left text-xs font-semibold text-gray-400">Exit Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800">
                        {backtestData.trades.map((trade, index) => (
                          <TradeRow key={trade.id || index} trade={trade} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Summary Box */}
              {backtestData.summary && (
                <div className="bg-gray-900 border border-primary-500/30 rounded-xl p-6">
                  <h3 className="text-sm font-semibold text-primary-400 uppercase tracking-wider mb-4">
                    Backtest Summary
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Ticker:</span>
                      <span className="text-white ml-2 font-semibold">{backtestData.summary.ticker}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Period:</span>
                      <span className="text-white ml-2">{backtestData.summary.period}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Initial:</span>
                      <span className="text-white ml-2">{formatCurrency(backtestData.summary.initial_capital ?? 0)}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Final:</span>
                      <span className={`ml-2 font-semibold ${(backtestData.summary.final_equity ?? 0) >= (backtestData.summary.initial_capital ?? 0) ? 'text-success-400' : 'text-danger-400'}`}>
                        {formatCurrency(backtestData.summary.final_equity ?? 0)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Return:</span>
                      <span className={`ml-2 font-semibold ${(backtestData.summary.total_return_pct ?? 0) >= 0 ? 'text-success-400' : 'text-danger-400'}`}>
                        {(backtestData.summary.total_return_pct ?? 0) >= 0 ? '+' : ''}{(backtestData.summary.total_return_pct ?? 0).toFixed(2)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Trades:</span>
                      <span className="text-white ml-2">{backtestData.summary.total_trades ?? 0}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Empty State */}
          {!backtestData && !loading && !error && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center justify-center text-center">
              <LineChart className="w-16 h-16 text-gray-700 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Ready to Backtest</h3>
              <p className="text-gray-400 max-w-md">
                Configure your backtest parameters and click "Run Backtest" to simulate historical trading
                performance based on the system's trading signals.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Metric Card Component
function MetricCard({
  icon,
  label,
  value,
  subtext,
  positive,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext?: string;
  positive?: boolean;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
        {icon}
        {label}
      </div>
      <div className={`text-xl font-bold ${positive === undefined ? 'text-white' : positive ? 'text-success-400' : 'text-danger-400'}`}>
        {value}
      </div>
      {subtext && (
        <div className={`text-xs mt-1 ${positive === undefined ? 'text-gray-500' : positive ? 'text-success-400/70' : 'text-danger-400/70'}`}>
          {subtext}
        </div>
      )}
    </div>
  );
}

// Trade Row Component
function TradeRow({ trade }: { trade: BacktestTrade }) {
  const isProfit = trade.pnl >= 0;

  return (
    <tr className="hover:bg-gray-800/50 transition-colors">
      <td className="px-4 py-3 text-sm text-white">
        {new Date(trade.entry_date).toLocaleDateString()}
      </td>
      <td className="px-4 py-3 text-sm text-white">
        {new Date(trade.exit_date).toLocaleDateString()}
      </td>
      <td className="px-4 py-3">
        <span className={`px-2 py-1 rounded text-xs font-semibold ${
          trade.side === 'LONG' ? 'bg-success-500/20 text-success-400' : 'bg-danger-500/20 text-danger-400'
        }`}>
          {trade.side}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-white text-right">
        ${trade.entry_price.toFixed(2)}
      </td>
      <td className="px-4 py-3 text-sm text-white text-right">
        ${trade.exit_price.toFixed(2)}
      </td>
      <td className="px-4 py-3 text-right">
        <div className={`flex items-center justify-end gap-1 ${isProfit ? 'text-success-400' : 'text-danger-400'}`}>
          {isProfit ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
          <span className="font-semibold">${Math.abs(trade.pnl).toFixed(2)}</span>
          <span className="text-xs">({isProfit ? '+' : ''}{(trade.pnl_pct * 100).toFixed(2)}%)</span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-400">
        {trade.exit_reason}
      </td>
    </tr>
  );
}
