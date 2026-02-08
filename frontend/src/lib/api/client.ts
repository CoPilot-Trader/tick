/**
 * API client for backend connection
 * Connects to the Multi-Agent Stock Prediction API
 */

import { StockData, PredictionPoint, PriceLevel } from '@/types';

// API base URL - configured via environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types for API Responses
// ============================================================================

export interface FusionSignalResponse {
  status: string;
  symbol: string;
  timestamp: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  fused_score: number;
  components: {
    price_forecast?: {
      signal: string;
      score: number;
      confidence: number;
      predicted_price?: number;
    };
    trend_classification?: {
      signal: string;
      score: number;
      confidence: number;
    };
    support_resistance?: {
      signal: string;
      score: number;
      confidence: number;
    };
    sentiment?: {
      signal: string;
      score: number;
      confidence: number;
    };
  };
  reasoning: string;
  weights: Record<string, number>;
  rules_applied: string[];
}

export interface BacktestRequest {
  ticker: string;
  days: number;
  initial_capital: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
}

export interface BacktestResult {
  status: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_equity: number;
  total_return: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  trades: BacktestTrade[];
  equity_curve: EquityPoint[];
  summary?: {
    ticker: string;
    period: string;
    initial_capital: number;
    final_equity: number;
    total_return_pct: number;
    total_trades: number;
  };
}

export interface BacktestTrade {
  id: string;
  symbol: string;
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  side: 'LONG' | 'SHORT';
  pnl: number;
  pnl_pct: number;
  exit_reason: string;
}

export interface EquityPoint {
  date: string;
  equity: number;
  drawdown: number;
}

export interface AlertRule {
  id: string;
  name: string;
  type: string;
  priority: string;
  enabled: boolean;
  cooldown_minutes: number;
}

export interface Alert {
  id: string;
  type: string;
  priority: string;
  symbol: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  rule_id: string;
  data?: Record<string, any>;
}

export interface AlertsSummary {
  status: string;
  total_alerts: number;
  unacknowledged: number;
  active_rules: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  by_symbol: Record<string, number>;
}

export interface TrendClassificationResponse {
  status: string;
  symbol: string;
  timeframe: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  probabilities: {
    BUY: number;
    SELL: number;
    HOLD: number;
  };
  confidence: number;
  model: string;
  features_used: number;
  timestamp: string;
}

export interface PriceForecastResponse {
  status: string;
  symbol: string;
  current_price: number;
  forecasts: {
    horizon: string;
    predicted_price: number;
    confidence: number;
    upper_bound: number;
    lower_bound: number;
    model: string;
  }[];
  timestamp: string;
}

export interface SentimentResponse {
  status: string;
  symbol: string;
  aggregated_sentiment: number;
  sentiment_label: 'positive' | 'negative' | 'neutral';
  confidence: number;
  impact: 'High' | 'Medium' | 'Low';
  news_count: number;
  time_weighted: boolean;
}

export interface LevelsResponse {
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

export interface HealthResponse {
  status: string;
  agent?: string;
  version?: string;
  [key: string]: any;
}

// ============================================================================
// API Client Class
// ============================================================================

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // ==========================================================================
  // Health Check
  // ==========================================================================

  async healthCheck(): Promise<HealthResponse> {
    return this.get('/health');
  }

  async fusionHealth(): Promise<HealthResponse> {
    return this.get('/api/v1/fusion/health');
  }

  async backtestHealth(): Promise<HealthResponse> {
    return this.get('/api/v1/backtest/health');
  }

  async alertsHealth(): Promise<HealthResponse> {
    return this.get('/api/v1/alerts/health');
  }

  // ==========================================================================
  // Fusion Agent - Trading Signals
  // ==========================================================================

  async getFusionSignal(symbol: string, days: number = 90): Promise<FusionSignalResponse> {
    return this.post(`/api/v1/fusion/${symbol}`, { days });
  }

  async getQuickFusionSignal(symbol: string): Promise<FusionSignalResponse> {
    return this.get(`/api/v1/fusion/${symbol}/quick`);
  }

  async getFusionConfig(): Promise<Record<string, any>> {
    return this.get('/api/v1/fusion/config');
  }

  // ==========================================================================
  // Backtesting
  // ==========================================================================

  async runBacktest(request: BacktestRequest): Promise<BacktestResult> {
    return this.post(`/api/v1/backtest/${request.ticker}`, request);
  }

  async runQuickBacktest(symbol: string, days: number = 180): Promise<BacktestResult> {
    return this.get(`/api/v1/backtest/${symbol}/quick?days=${days}`);
  }

  async getBacktestConfig(): Promise<Record<string, any>> {
    return this.get('/api/v1/backtest/config');
  }

  async updateBacktestConfig(config: Partial<BacktestRequest>): Promise<Record<string, any>> {
    return this.put('/api/v1/backtest/config', config);
  }

  // ==========================================================================
  // Alerts
  // ==========================================================================

  async getAlerts(params?: {
    ticker?: string;
    alert_type?: string;
    priority?: string;
    unacknowledged_only?: boolean;
    limit?: number;
  }): Promise<{ status: string; count: number; alerts: Alert[] }> {
    const searchParams = new URLSearchParams();
    if (params?.ticker) searchParams.set('ticker', params.ticker);
    if (params?.alert_type) searchParams.set('alert_type', params.alert_type);
    if (params?.priority) searchParams.set('priority', params.priority);
    if (params?.unacknowledged_only) searchParams.set('unacknowledged_only', 'true');
    if (params?.limit) searchParams.set('limit', params.limit.toString());

    const query = searchParams.toString();
    return this.get(`/api/v1/alerts${query ? `?${query}` : ''}`);
  }

  async getAlertsSummary(): Promise<AlertsSummary> {
    return this.get('/api/v1/alerts/summary');
  }

  async getAlertRules(): Promise<{ status: string; count: number; rules: AlertRule[] }> {
    return this.get('/api/v1/alerts/rules');
  }

  async checkAlerts(symbol: string, data: {
    signal?: string;
    confidence?: number;
    fused_score?: number;
    current_price?: number;
    sentiment_impact?: string;
    drawdown_pct?: number;
  }): Promise<{ status: string; triggered_alerts: Alert[] }> {
    return this.post(`/api/v1/alerts/check/${symbol}`, { ticker: symbol, ...data });
  }

  async acknowledgeAlert(alertId: string): Promise<{ status: string; message: string }> {
    return this.post(`/api/v1/alerts/${alertId}/acknowledge`, {});
  }

  async acknowledgeAllAlerts(ticker?: string): Promise<{ status: string; acknowledged_count: number }> {
    const query = ticker ? `?ticker=${ticker}` : '';
    return this.post(`/api/v1/alerts/acknowledge-all${query}`, {});
  }

  async clearAlerts(ticker?: string): Promise<{ status: string; cleared_count: number }> {
    const query = ticker ? `?ticker=${ticker}` : '';
    return this.delete(`/api/v1/alerts${query}`);
  }

  async enableRule(ruleId: string): Promise<{ status: string; message: string }> {
    return this.post(`/api/v1/alerts/rules/${ruleId}/enable`, {});
  }

  async disableRule(ruleId: string): Promise<{ status: string; message: string }> {
    return this.post(`/api/v1/alerts/rules/${ruleId}/disable`, {});
  }

  // ==========================================================================
  // Trend Classification
  // ==========================================================================

  async getTrendClassification(symbol: string, timeframe: string = '1d'): Promise<TrendClassificationResponse> {
    return this.get(`/api/v1/trend/${symbol}?timeframe=${timeframe}`);
  }

  // ==========================================================================
  // Price Forecast
  // ==========================================================================

  async getPriceForecast(symbol: string, horizons: string[] = ['1d']): Promise<PriceForecastResponse> {
    const horizonParam = horizons.join(',');
    const raw = await this.get<any>(`/api/v1/forecast/${symbol}?horizons=${horizonParam}&use_baseline=true&use_ensemble=false`);

    // Normalize backend response format:
    // Backend returns { predictions: { "1h": { price, confidence, price_lower, price_upper } } }
    // Frontend expects { forecasts: [{ horizon, predicted_price, confidence, upper_bound, lower_bound }] }
    if (raw.predictions && !raw.forecasts) {
      const forecasts = Object.entries(raw.predictions).map(([horizon, pred]: [string, any]) => ({
        horizon,
        predicted_price: pred.price,
        confidence: pred.confidence,
        upper_bound: pred.price_upper,
        lower_bound: pred.price_lower,
        model: pred.model || 'ensemble',
      }));
      return {
        status: raw.success ? 'success' : 'error',
        symbol: raw.ticker || symbol,
        current_price: raw.current_price,
        forecasts,
        timestamp: raw.generated_at || new Date().toISOString(),
      };
    }

    return raw;
  }

  // ==========================================================================
  // OHLCV Data
  // ==========================================================================

  async getOHLCV(symbol: string, timeframe: string = '5m', days: number = 1): Promise<{
    symbol: string;
    timeframe: string;
    count: number;
    data: { timestamp: string; open: number; high: number; low: number; close: number; volume: number }[];
  }> {
    return this.get(`/api/v1/data/${symbol}/ohlcv?timeframe=${timeframe}&days=${days}`);
  }

  // ==========================================================================
  // Sentiment
  // ==========================================================================

  async getSentiment(symbol: string): Promise<SentimentResponse> {
    return this.get(`/api/v1/sentiment/${symbol}/aggregate`);
  }

  async getNewsPipeline(symbol: string, minRelevance: number = 0.3, maxArticles: number = 10): Promise<any> {
    return this.post('/api/v1/news-pipeline/visualize', {
      symbol,
      min_relevance: minRelevance,
      max_articles: maxArticles,
    });
  }

  // ==========================================================================
  // Support & Resistance Levels
  // ==========================================================================

  async getLevels(symbol: string, params?: {
    min_strength?: number;
    max_levels?: number;
    timeframe?: string;
  }): Promise<LevelsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.min_strength) searchParams.set('min_strength', params.min_strength.toString());
    if (params?.max_levels) searchParams.set('max_levels', params.max_levels.toString());
    if (params?.timeframe) searchParams.set('timeframe', params.timeframe);

    const query = searchParams.toString();
    return this.get(`/api/v1/levels/${symbol}${query ? `?${query}` : ''}`);
  }

  // ==========================================================================
  // Combined Stock Data (for dashboard)
  // ==========================================================================

  /**
   * Get comprehensive stock data by calling multiple endpoints
   * This aggregates data from fusion, forecast, trend, levels, and sentiment
   */
  async getStockData(symbol: string): Promise<StockData> {
    try {
      // Fetch real OHLCV data, forecast, and levels in parallel
      const [ohlcvResult, forecastResult, levels] = await Promise.all([
        this.getOHLCV(symbol, '5m', 1).catch(() => null),
        this.getPriceForecast(symbol, ['1h']).catch(() => null),
        this.getLevels(symbol, { max_levels: 3 }).catch(() => null),
      ]);

      // Use real OHLCV data if available, otherwise generate intraday fallback
      let historical_data: { timestamp: string; open: number; high: number; low: number; close: number; volume: number }[];
      if (ohlcvResult && ohlcvResult.data && ohlcvResult.data.length > 0) {
        historical_data = ohlcvResult.data;
      } else {
        const fallbackPrice = levels?.current_price || 100;
        historical_data = this.generateIntradayData(fallbackPrice);
      }

      const currentPrice = historical_data.length > 0
        ? historical_data[historical_data.length - 1].close
        : (levels?.current_price || 100);

      // Calculate price change from historical data
      const firstPrice = historical_data[0]?.close || currentPrice;
      const price_change = currentPrice - firstPrice;
      const price_change_percent = ((currentPrice - firstPrice) / firstPrice) * 100;

      // Build predictions from the 1h forecast
      const predictions: PredictionPoint[] = [];
      const forecast1h = forecastResult?.forecasts?.find(f => f.horizon === '1h');
      if (forecast1h) {
        // Interpolate 6 prediction points at 10-min intervals over the next hour
        const targetPrice = forecast1h.predicted_price;
        const upperTarget = forecast1h.upper_bound;
        const lowerTarget = forecast1h.lower_bound;
        const confidence = forecast1h.confidence;

        for (let i = 1; i <= 6; i++) {
          const fraction = i / 6;
          const futureDate = new Date();
          futureDate.setMinutes(futureDate.getMinutes() + i * 10);

          const interpolatedPrice = currentPrice + (targetPrice - currentPrice) * fraction;
          const interpolatedUpper = currentPrice + (upperTarget - currentPrice) * fraction;
          const interpolatedLower = currentPrice + (lowerTarget - currentPrice) * fraction;

          predictions.push({
            timestamp: futureDate.toISOString(),
            predicted_price: interpolatedPrice,
            confidence: confidence,
            upper_bound: interpolatedUpper,
            lower_bound: interpolatedLower,
            support_levels: levels?.support_levels || [],
            resistance_levels: levels?.resistance_levels || [],
          });
        }
      }

      return {
        symbol,
        name: symbol,
        current_price: currentPrice,
        price_change,
        price_change_percent,
        historical_data,
        predictions,
        support_levels: levels?.support_levels || [],
        resistance_levels: levels?.resistance_levels || [],
        last_updated: new Date().toISOString(),
      };
    } catch (error) {
      console.error(`Error fetching stock data for ${symbol}:`, error);
      const fallbackPrice = 100;
      return {
        symbol,
        name: symbol,
        current_price: fallbackPrice,
        price_change: 0,
        price_change_percent: 0,
        historical_data: this.generateIntradayData(fallbackPrice),
        predictions: [],
        support_levels: [],
        resistance_levels: [],
        last_updated: new Date().toISOString(),
      };
    }
  }

  /**
   * Generate simulated intraday OHLCV data (5-min intervals for 1 trading day) as fallback
   */
  private generateIntradayData(currentPrice: number) {
    const data = [];
    const volatility = 0.001; // 0.1% per 5-min candle
    let price = currentPrice * 0.995; // Start slightly lower

    // Generate ~78 bars (6.5 hours of trading at 5-min intervals)
    const now = new Date();
    const marketOpen = new Date(now);
    marketOpen.setHours(9, 30, 0, 0);

    for (let i = 0; i < 78; i++) {
      const barTime = new Date(marketOpen.getTime() + i * 5 * 60 * 1000);
      if (barTime > now) break;

      const barReturn = (Math.random() - 0.48) * volatility;
      price = price * (1 + barReturn);

      const open = price * (1 + (Math.random() - 0.5) * 0.001);
      const high = Math.max(price, open) * (1 + Math.random() * 0.002);
      const low = Math.min(price, open) * (1 - Math.random() * 0.002);
      const close = price;
      const volume = Math.floor(50000 + Math.random() * 500000);

      data.push({
        timestamp: barTime.toISOString(),
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume,
      });
    }

    if (data.length > 0) {
      data[data.length - 1].close = currentPrice;
    }

    return data;
  }

  // ==========================================================================
  // HTTP Methods
  // ==========================================================================

  private async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  private async post<T>(endpoint: string, body: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  private async put<T>(endpoint: string, body: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  private async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
