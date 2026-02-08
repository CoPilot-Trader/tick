'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Bell,
  ChevronDown,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Shield,
  AlertTriangle,
  Info,
  Trash2,
  RefreshCw,
  ToggleLeft,
  ToggleRight,
  BellRing,
  BellOff,
  Filter,
} from 'lucide-react';
import { SP500_STOCKS } from '@/lib/mockData';
import { apiClient, Alert, AlertRule, AlertsSummary } from '@/lib/api/client';

export default function AlertsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [summary, setSummary] = useState<AlertsSummary | null>(null);
  const [filterType, setFilterType] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<string>('');
  const [showUnacknowledgedOnly, setShowUnacknowledgedOnly] = useState(false);
  const [activeTab, setActiveTab] = useState<'alerts' | 'rules'>('alerts');

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [alertsRes, rulesRes, summaryRes] = await Promise.all([
        apiClient.getAlerts({
          alert_type: filterType || undefined,
          priority: filterPriority || undefined,
          unacknowledged_only: showUnacknowledgedOnly,
        }),
        apiClient.getAlertRules(),
        apiClient.getAlertsSummary(),
      ]);

      setAlerts(alertsRes.alerts || []);
      setRules(rulesRes.rules || []);
      setSummary(summaryRes);
    } catch (err) {
      setError(`Failed to load alerts: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterType, filterPriority, showUnacknowledgedOnly]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await apiClient.acknowledgeAlert(alertId);
      await loadData();
    } catch (err) {
      setError(`Failed to acknowledge alert: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleAcknowledgeAll = async () => {
    try {
      await apiClient.acknowledgeAllAlerts();
      await loadData();
    } catch (err) {
      setError(`Failed to acknowledge alerts: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear all alerts?')) return;
    try {
      await apiClient.clearAlerts();
      await loadData();
    } catch (err) {
      setError(`Failed to clear alerts: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      if (enabled) {
        await apiClient.disableRule(ruleId);
      } else {
        await apiClient.enableRule(ruleId);
      }
      await loadData();
    } catch (err) {
      setError(`Failed to toggle rule: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return { bg: 'bg-danger-500/20', text: 'text-danger-400', border: 'border-danger-500/50' };
      case 'high':
        return { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/50' };
      case 'medium':
        return { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/50' };
      case 'low':
        return { bg: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500/50' };
      default:
        return { bg: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500/50' };
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'signal':
        return <BellRing className="w-4 h-4" />;
      case 'price':
        return <AlertTriangle className="w-4 h-4" />;
      case 'risk':
        return <Shield className="w-4 h-4" />;
      case 'performance':
        return <Info className="w-4 h-4" />;
      default:
        return <Bell className="w-4 h-4" />;
    }
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
              <Bell className="w-5 h-5 text-primary-500" />
              <h1 className="text-lg font-bold text-white">Alerts</h1>
            </div>
          </div>
          <div className="flex-shrink-0">
            <p className="text-xs text-gray-400 hidden sm:block">TICK - Alert Management</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full p-4 md:p-6 pb-12">
        <div className="max-w-[1400px] mx-auto">
          {/* Summary Cards */}
          {summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
                  <Bell className="w-4 h-4" />
                  Total Alerts
                </div>
                <div className="text-2xl font-bold text-white">{summary.total_alerts}</div>
              </div>
              <div className="bg-gray-900 border border-amber-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 text-amber-400 text-xs font-medium mb-2">
                  <AlertCircle className="w-4 h-4" />
                  Unacknowledged
                </div>
                <div className="text-2xl font-bold text-amber-400">{summary.unacknowledged}</div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
                  <Shield className="w-4 h-4" />
                  Active Rules
                </div>
                <div className="text-2xl font-bold text-white">{summary.active_rules}</div>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 text-gray-400 text-xs font-medium mb-2">
                  <Filter className="w-4 h-4" />
                  By Priority
                </div>
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(summary.by_priority || {}).map(([priority, count]) => (
                    <span
                      key={priority}
                      className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(priority).bg} ${getPriorityColor(priority).text}`}
                    >
                      {priority}: {count}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'alerts'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              <span className="flex items-center gap-2">
                <Bell className="w-4 h-4" />
                Alerts ({alerts.length})
              </span>
            </button>
            <button
              onClick={() => setActiveTab('rules')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'rules'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              <span className="flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Rules ({rules.length})
              </span>
            </button>
          </div>

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
              <p className="text-gray-400">Loading alerts...</p>
            </div>
          )}

          {/* Alerts Tab */}
          {!loading && activeTab === 'alerts' && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              {/* Filters & Actions */}
              <div className="p-4 border-b border-gray-800 flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap items-center gap-3">
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All Types</option>
                    <option value="signal">Signal</option>
                    <option value="price">Price</option>
                    <option value="risk">Risk</option>
                    <option value="performance">Performance</option>
                  </select>
                  <select
                    value={filterPriority}
                    onChange={(e) => setFilterPriority(e.target.value)}
                    className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All Priorities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                  <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showUnacknowledgedOnly}
                      onChange={(e) => setShowUnacknowledgedOnly(e.target.checked)}
                      className="rounded bg-gray-800 border-gray-600 text-primary-500 focus:ring-primary-500"
                    />
                    Unacknowledged only
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={loadData}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm flex items-center gap-2 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                  </button>
                  <button
                    onClick={handleAcknowledgeAll}
                    className="px-3 py-1.5 bg-primary-600 hover:bg-primary-500 text-white rounded-lg text-sm flex items-center gap-2 transition-colors"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Acknowledge All
                  </button>
                  <button
                    onClick={handleClearAll}
                    className="px-3 py-1.5 bg-danger-600 hover:bg-danger-500 text-white rounded-lg text-sm flex items-center gap-2 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    Clear All
                  </button>
                </div>
              </div>

              {/* Alerts List */}
              {alerts.length === 0 ? (
                <div className="p-12 text-center">
                  <BellOff className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">No Alerts</h3>
                  <p className="text-gray-400">No alerts match your current filters.</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {alerts.map((alert) => (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      onAcknowledge={() => handleAcknowledge(alert.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Rules Tab */}
          {!loading && activeTab === 'rules' && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-gray-800">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                  Alert Rules Configuration
                </h3>
              </div>
              {rules.length === 0 ? (
                <div className="p-12 text-center">
                  <Shield className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">No Rules</h3>
                  <p className="text-gray-400">No alert rules configured.</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {rules.map((rule) => (
                    <RuleCard
                      key={rule.id}
                      rule={rule}
                      onToggle={() => handleToggleRule(rule.id, rule.enabled)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Alert Card Component
function AlertCard({ alert, onAcknowledge }: { alert: Alert; onAcknowledge: () => void }) {
  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return { bg: 'bg-danger-500/20', text: 'text-danger-400', border: 'border-danger-500/50' };
      case 'high':
        return { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/50' };
      case 'medium':
        return { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/50' };
      default:
        return { bg: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500/50' };
    }
  };

  const colors = getPriorityColor(alert.priority);

  return (
    <div className={`p-4 hover:bg-gray-800/50 transition-colors ${!alert.acknowledged ? colors.bg : ''}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${colors.bg} ${colors.text}`}>
              {alert.priority}
            </span>
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400">
              {alert.type}
            </span>
            {alert.symbol && (
              <span className="text-xs font-semibold text-primary-400">{alert.symbol}</span>
            )}
            {!alert.acknowledged && (
              <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-400">
                NEW
              </span>
            )}
          </div>
          <p className="text-white">{alert.message}</p>
          <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            {new Date(alert.timestamp).toLocaleString()}
          </div>
        </div>
        {!alert.acknowledged && (
          <button
            onClick={onAcknowledge}
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm flex items-center gap-2 transition-colors"
          >
            <CheckCircle2 className="w-4 h-4" />
            Acknowledge
          </button>
        )}
      </div>
    </div>
  );
}

// Rule Card Component
function RuleCard({ rule, onToggle }: { rule: AlertRule; onToggle: () => void }) {
  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return 'text-danger-400';
      case 'high':
        return 'text-orange-400';
      case 'medium':
        return 'text-amber-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="p-4 hover:bg-gray-800/50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <span className="font-semibold text-white">{rule.name}</span>
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-800 text-gray-400">
              {rule.type}
            </span>
            <span className={`text-xs font-semibold ${getPriorityColor(rule.priority)}`}>
              {rule.priority.toUpperCase()}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>ID: {rule.id}</span>
            <span>Cooldown: {rule.cooldown_minutes} min</span>
          </div>
        </div>
        <button
          onClick={onToggle}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            rule.enabled
              ? 'bg-success-500/20 text-success-400 hover:bg-success-500/30'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          {rule.enabled ? (
            <>
              <ToggleRight className="w-5 h-5" />
              Enabled
            </>
          ) : (
            <>
              <ToggleLeft className="w-5 h-5" />
              Disabled
            </>
          )}
        </button>
      </div>
    </div>
  );
}
