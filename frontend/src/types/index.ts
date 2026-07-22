// Type definitions matching backend interfaces

export interface OHLCVDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceForecast {
  horizon: string; // "1h", "4h", "1d", "1w"
  predicted_price: number;
  confidence: number; // 0.0 to 1.0
  upper_bound: number;
  lower_bound: number;
  model: string; // "prophet" or "lstm"
}

export interface TrendClassification {
  signal: "BUY" | "SELL" | "HOLD";
  probabilities: {
    BUY: number;
    SELL: number;
    HOLD: number;
  };
  confidence: number;
  model: string;
}

export interface PriceLevel {
  price: number;
  strength: number; // 0-100
  type: "support" | "resistance";
  touches: number;
  validated: boolean;
}

export interface PsychologicalLevel {
  price: number;
  side: "support" | "resistance";
  type: "psychological";
  distance_pct: number;
}

export interface SentimentData {
  sentiment_score: number; // -1.0 to +1.0
  sentiment_label: "positive" | "neutral" | "negative";
  confidence: number;
  news_count: number;
  impact: "High" | "Medium" | "Low";
}

export interface NewsEvent {
  timestamp: string;
  title: string;
  source: string;
  sentiment: number;
  impact: "High" | "Medium" | "Low";
}

export interface TechnicalIndicator {
  rsi?: number;
  macd?: number;
  bb_upper?: number;
  bb_lower?: number;
  sma_50?: number;
  sma_200?: number;
  volume_ma?: number;
}

export interface PredictionPoint {
  timestamp: string;
  actual_price?: number;
  predicted_price: number;
  confidence: number;
  upper_bound: number;
  lower_bound: number;
  trend?: TrendClassification;
  sentiment?: SentimentData;
  support_levels?: PriceLevel[];
  resistance_levels?: PriceLevel[];
  fused_signal?: "BUY" | "SELL" | "HOLD";
  fused_confidence?: number;
  technical_indicators?: TechnicalIndicator;
  news_events?: NewsEvent[];
  timing_score?: number;
  volatility?: number;
}

export interface PredictionHistoryEntry {
  predicted_at: string;
  horizon: string;
  base_price: number;
  predicted_price: number;
  confidence: number;
  direction: string;
  target_date: string;
  target_timestamp?: string;
  actual_price: number | null;
  error_pct: number | null;
  direction_correct: boolean | null;
  source?: string; // "tick" (default) or "pcr_shock"
}

export interface LevelRejectionSignal {
  ticker: string;
  signal_time: string;
  level_type: string;       // SESSION_VWAP, PDL_resist, etc.
  level_price?: number;
  entry_price: number;
  target1_price: number;
  target2_price: number | null;
  stop_price: number;
  side: string;             // CALL / PUT
  vix_level?: number;
  macro_regime?: string;
  // Tri-state: 1=hit, 0=not-hit, null=pending (outcome not evaluated yet).
  // Null must NEVER be treated as 0 — a pending signal isn't a miss.
  target1_hit: 1 | 0 | null;
  target2_hit?: 1 | 0 | null;
  stop_hit: 1 | 0 | null;
  outcome_filled?: boolean;
  // spot_at_signal is aliased to entry_price in the raw feed. Kept for
  // downstream code that references it separately.
  spot_at_signal?: number;
  // Number of structural levels the bar rejected off (PML, VWAP, EMA200,
  // pivots, etc). >1 = confluence — signals with more levels tend to
  // carry more conviction. Feed publishes one row per signal after
  // Tory's 2026-07-21 collapse; this preserves the multi-level count.
  levels_at_bar?: number;
}

export interface PredictionAccuracy {
  mape: number;
  directional_accuracy: number;
  total_predictions: number;
  resolved: number;
}

export interface StockData {
  symbol: string;
  name: string;
  current_price: number;
  price_change: number;
  price_change_percent: number;
  historical_data: OHLCVDataPoint[];
  predictions: PredictionPoint[];
  support_levels: PriceLevel[];
  resistance_levels: PriceLevel[];
  psychological_levels?: PsychologicalLevel[];
  news_events?: NewsEvent[];
  prediction_history?: PredictionHistoryEntry[];
  prediction_accuracy?: PredictionAccuracy | null;
  level_rejection_signals?: LevelRejectionSignal[];
  last_updated: string;
}

export interface StockOption {
  symbol: string;
  name: string;
}

export interface GraphFilters {
  showActualPrice: boolean;
  showPredictedPrice: boolean;
  showSupportResistance: boolean;
  showConfidenceBounds: boolean;
  showVolume: boolean;
  showRSI: boolean;
  showMACD: boolean;
  showBollingerBands: boolean;
  showMovingAverages: boolean;
  showEMA9: boolean;
  showEMA21: boolean;
  showEMA50: boolean;
  showNewsEvents: boolean;
  showTimingSignals: boolean;
  showPredictionAccuracy: boolean;
  showLevelRejection: boolean;
  showVWAP: boolean;
}
