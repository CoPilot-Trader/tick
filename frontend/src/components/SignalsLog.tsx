'use client';

import { useEffect, useState, useMemo } from 'react';
import { X, TrendingUp, TrendingDown, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { LevelRejectionSignal } from '@/types';
import { formatEasternTime, formatEasternDate } from '@/lib/time';

interface PCRShockSignal {
  ticker: string;
  signal_ts: string;
  signal_type: string;
  spot_at_signal: number;
  fwd_15m_pct: number | null;
  fwd_30m_pct: number | null;
  fwd_1h_pct: number | null;
  fwd_4h_pct: number | null;
  fwd_1d_pct: number | null;
  outcome_class: string | null;
  accuracy: string | null;
}

interface UnifiedSignal {
  source: 'level_rejection' | 'pcr_shock';
  timestamp: string;
  raw: LevelRejectionSignal | PCRShockSignal;
}

interface SignalsLogProps {
  symbol: string;
  open: boolean;
  onClose: () => void;
  onSignalClick?: (signalTimeISO: string) => void;
}

export default function SignalsLog({ symbol, open, onClose, onSignalClick }: SignalsLogProps) {
  const [levelRej, setLevelRej] = useState<LevelRejectionSignal[]>([]);
  const [pcrShock, setPcrShock] = useState<PCRShockSignal[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'level_rejection' | 'pcr_shock'>('all');

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    Promise.all([
      apiClient.getLevelRejectionSignals(symbol).catch(() => null),
      // Use raw PCR shock for the log (richer fields than the backtrack reshape)
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/signals/pcr-shock/${symbol}`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null),
    ]).then(([lrResp, pcrResp]) => {
      if (cancelled) return;
      setLevelRej(lrResp?.signals || []);
      setPcrShock(pcrResp?.signals || []);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [symbol, open]);

  const merged: UnifiedSignal[] = useMemo(() => {
    const items: UnifiedSignal[] = [];
    for (const s of levelRej) items.push({ source: 'level_rejection', timestamp: s.signal_time, raw: s });
    for (const s of pcrShock) items.push({ source: 'pcr_shock', timestamp: s.signal_ts, raw: s });
    items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    if (filter === 'all') return items;
    return items.filter(i => i.source === filter);
  }, [levelRej, pcrShock, filter]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.5)' }}
        onClick={onClose}
      />

      {/* Slide-in panel */}
      <div
        className="fixed top-0 right-0 z-50 h-full flex flex-col shadow-2xl"
        style={{ background: '#131722', borderLeft: '1px solid #2a2e39', width: 'min(640px, 90vw)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 flex-shrink-0" style={{ background: '#1e222d', borderBottom: '1px solid #2a2e39' }}>
          <div>
            <h2 className="text-sm font-semibold" style={{ color: '#d1d4dc' }}>
              Signals Log — <span style={{ color: '#2962ff' }}>{symbol}</span>
            </h2>
            <p className="text-[10px] mt-0.5" style={{ color: '#787b86' }}>
              Audit trail of signals received from the VM pipeline
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-[#2a2e39] transition-colors"
            style={{ color: '#787b86' }}
            aria-label="Close signals log"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 px-3 py-2 flex-shrink-0" style={{ background: '#1e222d', borderBottom: '1px solid #2a2e39' }}>
          {[
            { key: 'all', label: `All (${levelRej.length + pcrShock.length})` },
            { key: 'level_rejection', label: `Level Rejection (${levelRej.length})` },
            { key: 'pcr_shock', label: `PCR Shock (${pcrShock.length})` },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key as typeof filter)}
              className="px-3 py-1 text-[11px] font-medium rounded transition-all"
              style={{
                background: filter === tab.key ? '#2962ff20' : 'transparent',
                color: filter === tab.key ? '#2962ff' : '#787b86',
                border: filter === tab.key ? '1px solid #2962ff40' : '1px solid transparent',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2" style={{ borderColor: '#2962ff' }} />
            </div>
          )}

          {!loading && merged.length === 0 && (
            <div className="px-4 py-12 text-center">
              <p className="text-sm" style={{ color: '#787b86' }}>No signals for {symbol} yet.</p>
              <p className="text-xs mt-1" style={{ color: '#5c6272' }}>
                Signals will appear here as they are generated by the VM pipeline.
              </p>
            </div>
          )}

          {!loading && merged.length > 0 && (
            <div className="divide-y" style={{ borderColor: '#2a2e39' }}>
              {merged.map((item, idx) => (
                <SignalRow
                  key={`${item.source}-${idx}`}
                  item={item}
                  onClick={() => {
                    if (onSignalClick) onSignalClick(item.timestamp);
                    onClose();
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 text-[10px] flex-shrink-0" style={{ background: '#1e222d', borderTop: '1px solid #2a2e39', color: '#787b86' }}>
          Source: <code style={{ color: '#2962ff' }}>signal_bridge</code> · {merged.length} entries · Newest first
        </div>
      </div>
    </>
  );
}

function SignalRow({ item, onClick }: { item: UnifiedSignal; onClick?: () => void }) {
  if (item.source === 'level_rejection') {
    const s = item.raw as LevelRejectionSignal;
    // Tri-state hit flags — null means pending (outcome not yet evaluated),
    // never conflate with 0. `outcome_filled` on the feed is the source of
    // truth; the flags corroborate. Some legacy rows still lack outcome_filled,
    // so we fall back to the flag check.
    const outcomeFilled = s.outcome_filled ?? (s.target1_hit !== null || s.stop_hit !== null);
    const won = s.target1_hit === 1;
    const stopped = s.stop_hit === 1;
    const pending = !outcomeFilled;
    const isPut = (s.side || '').toUpperCase() === 'PUT';
    return (
      <div onClick={onClick} className="px-4 py-3 hover:bg-[#1e222d] transition-colors cursor-pointer" title="Click to zoom the chart to this signal">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold" style={{ background: '#00bcd420', color: '#00bcd4', border: '1px solid #00bcd440' }}>
                LEVEL REJECTION
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: '#1e222d', color: '#787b86' }}>
                {s.level_type}
              </span>
              <span className="text-[10px] font-semibold" style={{ color: isPut ? '#ef5350' : '#26a69a' }}>
                {isPut ? 'PUT' : 'CALL'}
              </span>
              {(s.levels_at_bar ?? 0) > 1 && (
                <span
                  className="text-[9px] font-bold px-1.5 py-0.5 rounded"
                  style={{ background: '#ffb74d20', color: '#ffb74d', border: '1px solid #ffb74d40' }}
                  title={`Rejected off ${s.levels_at_bar} structural levels at this bar — confluence signal`}
                >
                  ×{s.levels_at_bar}
                </span>
              )}
              <OutcomePill won={won} stopped={stopped} pending={pending} />
            </div>
            <div className="grid grid-cols-4 gap-2 text-[11px] font-mono">
              <Field label="Entry" value={s.entry_price.toFixed(2)} color="#ffc107" />
              <Field label="Stop" value={s.stop_price.toFixed(2)} color="#ef5350" />
              <Field label="T1" value={s.target1_price.toFixed(2)} color="#4caf50" />
              <Field label="T2" value={s.target2_price != null ? s.target2_price.toFixed(2) : '—'} color="#8bc34a" />
            </div>
            {(s.vix_level != null || s.macro_regime) && (
              <div className="flex items-center gap-3 mt-1.5 text-[10px]" style={{ color: '#787b86' }}>
                {s.vix_level != null && (
                  <span>VIX <span style={{ color: '#d1d4dc' }}>{s.vix_level.toFixed(2)}</span></span>
                )}
                {s.vix_level != null && s.macro_regime && <span>·</span>}
                {s.macro_regime && (
                  <span>Regime <span style={{ color: '#d1d4dc' }}>{s.macro_regime}</span></span>
                )}
              </div>
            )}
          </div>
          <div className="text-right flex-shrink-0">
            <div className="text-[10px]" style={{ color: '#787b86' }}>{formatTime(s.signal_time)}</div>
            <div className="text-[9px] mt-0.5" style={{ color: '#5c6272' }}>{formatDate(s.signal_time)}</div>
          </div>
        </div>
      </div>
    );
  }

  // PCR Shock
  const s = item.raw as PCRShockSignal;
  const isUp = (s.fwd_1d_pct ?? 0) >= 0;
  const outcomeColor =
    s.outcome_class === 'STRONG_WIN' ? '#26a69a' :
    s.outcome_class === 'WIN' ? '#4caf50' :
    s.outcome_class === 'LOSS' ? '#ef5350' :
    s.outcome_class === 'FLAT' ? '#787b86' : '#ffb74d';

  return (
    <div onClick={onClick} className="px-4 py-3 hover:bg-[#1e222d] transition-colors cursor-pointer" title="Click to zoom the chart to this signal">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold" style={{ background: '#ff980020', color: '#ff9800', border: '1px solid #ff980040' }}>
              PCR SHOCK
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: '#1e222d', color: '#787b86' }}>
              {s.signal_type}
            </span>
            {s.outcome_class && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ color: outcomeColor, border: `1px solid ${outcomeColor}40` }}>
                {s.outcome_class}
              </span>
            )}
            {s.accuracy && (
              <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ color: '#787b86', background: '#1e222d' }}>
                {s.accuracy}
              </span>
            )}
          </div>
          <div className="grid grid-cols-5 gap-2 text-[11px] font-mono">
            <Field label="Spot" value={s.spot_at_signal.toFixed(2)} color="#d1d4dc" />
            <Field label="15m" value={fmtPct(s.fwd_15m_pct)} color={pctColor(s.fwd_15m_pct)} />
            <Field label="1h" value={fmtPct(s.fwd_1h_pct)} color={pctColor(s.fwd_1h_pct)} />
            <Field label="4h" value={fmtPct(s.fwd_4h_pct)} color={pctColor(s.fwd_4h_pct)} />
            <Field label="1d" value={fmtPct(s.fwd_1d_pct)} color={pctColor(s.fwd_1d_pct)} />
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-[10px]" style={{ color: '#787b86' }}>{formatTime(s.signal_ts)}</div>
          <div className="text-[9px] mt-0.5" style={{ color: '#5c6272' }}>{formatDate(s.signal_ts)}</div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <div className="text-[9px] uppercase tracking-wide" style={{ color: '#5c6272' }}>{label}</div>
      <div style={{ color }}>{value}</div>
    </div>
  );
}

function OutcomePill({ won, stopped, pending }: { won: boolean; stopped: boolean; pending: boolean }) {
  if (pending) {
    return (
      <span className="text-[9px] font-semibold flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ background: '#ffb74d20', color: '#ffb74d', border: '1px solid #ffb74d40' }}>
        <Clock className="w-2.5 h-2.5" /> PENDING
      </span>
    );
  }
  if (won) {
    return (
      <span className="text-[9px] font-semibold flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ background: '#4caf5020', color: '#4caf50', border: '1px solid #4caf5040' }}>
        <CheckCircle2 className="w-2.5 h-2.5" /> WON · T1 HIT
      </span>
    );
  }
  return (
    <span className="text-[9px] font-semibold flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ background: '#ef535020', color: '#ef5350', border: '1px solid #ef535040' }}>
      <XCircle className="w-2.5 h-2.5" /> STOPPED
    </span>
  );
}

function fmtPct(v: number | null): string {
  if (v == null) return '—';
  return (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
}

function pctColor(v: number | null): string {
  if (v == null) return '#5c6272';
  return v >= 0 ? '#26a69a' : '#ef5350';
}

function formatTime(iso: string): string {
  return formatEasternTime(iso, true) || iso;
}

function formatDate(iso: string): string {
  return formatEasternDate(iso) || iso;
}
