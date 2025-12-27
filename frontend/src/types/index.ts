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
  trend: TrendClassification;
  sentiment: SentimentData;
  support_levels: PriceLevel[];
  resistance_levels: PriceLevel[];
  fused_signal: "BUY" | "SELL" | "HOLD";
  fused_confidence: number;
  technical_indicators?: TechnicalIndicator;
  news_events?: NewsEvent[];
  timing_score?: number;
  volatility?: number;
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
  showNewsEvents: boolean;
  showTimingSignals: boolean;
}
