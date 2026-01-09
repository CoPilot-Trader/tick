import { StockData, PredictionPoint, OHLCVDataPoint, PriceLevel, TrendClassification, SentimentData, TechnicalIndicator, NewsEvent } from '@/types';

// S&P 500 stocks organized by sector
export const SP500_STOCKS = [
  // Technology
  { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology' },
  { symbol: 'MSFT', name: 'Microsoft Corporation', sector: 'Technology' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology' },
  { symbol: 'GOOG', name: 'Alphabet Inc. (Class C)', sector: 'Technology' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', sector: 'Technology' },
  { symbol: 'META', name: 'Meta Platforms Inc.', sector: 'Technology' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation', sector: 'Technology' },
  { symbol: 'TSLA', name: 'Tesla Inc.', sector: 'Technology' },
  { symbol: 'NFLX', name: 'Netflix Inc.', sector: 'Technology' },
  { symbol: 'INTC', name: 'Intel Corporation', sector: 'Technology' },
  // Energy
  { symbol: 'XOM', name: 'Exxon Mobil Corporation', sector: 'Energy' },
  { symbol: 'CVX', name: 'Chevron Corporation', sector: 'Energy' },
  { symbol: 'SLB', name: 'Schlumberger Limited', sector: 'Energy' },
  { symbol: 'COP', name: 'ConocoPhillips', sector: 'Energy' },
  { symbol: 'EOG', name: 'EOG Resources Inc.', sector: 'Energy' },
  // Healthcare
  { symbol: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare' },
  { symbol: 'PFE', name: 'Pfizer Inc.', sector: 'Healthcare' },
  { symbol: 'UNH', name: 'UnitedHealth Group Inc.', sector: 'Healthcare' },
  { symbol: 'ABBV', name: 'AbbVie Inc.', sector: 'Healthcare' },
  { symbol: 'TMO', name: 'Thermo Fisher Scientific Inc.', sector: 'Healthcare' },
  // Finance
  { symbol: 'JPM', name: 'JPMorgan Chase & Co.', sector: 'Finance' },
  { symbol: 'BAC', name: 'Bank of America Corp.', sector: 'Finance' },
  { symbol: 'GS', name: 'Goldman Sachs Group Inc.', sector: 'Finance' },
  { symbol: 'MS', name: 'Morgan Stanley', sector: 'Finance' },
  { symbol: 'WFC', name: 'Wells Fargo & Company', sector: 'Finance' },
  { symbol: 'BRK.B', name: 'Berkshire Hathaway Inc.', sector: 'Finance' },
  { symbol: 'V', name: 'Visa Inc.', sector: 'Finance' },
  // Consumer
  { symbol: 'WMT', name: 'Walmart Inc.', sector: 'Consumer' },
  { symbol: 'PG', name: 'The Procter & Gamble Company', sector: 'Consumer' },
  { symbol: 'KO', name: 'The Coca-Cola Company', sector: 'Consumer' },
  { symbol: 'PEP', name: 'PepsiCo Inc.', sector: 'Consumer' },
  { symbol: 'MCD', name: "McDonald's Corporation", sector: 'Consumer' },
];

// Generate mock historical data - last 24 hours with 5-minute intervals
function generateHistoricalData(symbol: string, basePrice: number): OHLCVDataPoint[] {
  const data: OHLCVDataPoint[] = [];
  const now = new Date();
  let currentPrice = basePrice;
  
  // Generate last 24 hours (288 intervals of 5 minutes)
  for (let i = 287; i >= 0; i--) {
    const timestamp = new Date(now);
    timestamp.setMinutes(timestamp.getMinutes() - i * 5);
    
    // Random walk with slight upward bias
    const change = (Math.random() - 0.45) * 0.015;
    currentPrice = Math.max(basePrice * 0.85, currentPrice * (1 + change));
    
    // Round to 2 decimal places for clean prices
    currentPrice = Math.round(currentPrice * 100) / 100;
    
    const high = Math.round(currentPrice * (1 + Math.random() * 0.01) * 100) / 100;
    const low = Math.round(currentPrice * (1 - Math.random() * 0.01) * 100) / 100;
    const open = i === 287 ? currentPrice : data[data.length - 1].close;
    const close = Math.round(currentPrice * (1 + (Math.random() - 0.5) * 0.005) * 100) / 100;
    
    data.push({
      timestamp: timestamp.toISOString(),
      open,
      high,
      low,
      close,
      volume: Math.floor(Math.random() * 1000000) + 500000,
    });
  }
  
  return data;
}

// Generate technical indicators
function generateTechnicalIndicators(prices: number[], currentPrice: number): TechnicalIndicator {
  const recentPrices = prices.slice(-50);
  const avg50 = recentPrices.reduce((a, b) => a + b, 0) / recentPrices.length;
  const avg200 = prices.length >= 200 
    ? prices.slice(-200).reduce((a, b) => a + b, 0) / 200 
    : avg50;
  
  // Simple RSI calculation
  const gains = recentPrices.slice(1).map((p, i) => p > recentPrices[i] ? p - recentPrices[i] : 0);
  const losses = recentPrices.slice(1).map((p, i) => p < recentPrices[i] ? recentPrices[i] - p : 0);
  const avgGain = gains.reduce((a, b) => a + b, 0) / gains.length;
  const avgLoss = losses.reduce((a, b) => a + b, 0) / losses.length;
  const rsi = avgLoss === 0 ? 100 : 100 - (100 / (1 + avgGain / avgLoss));
  
  // Simple MACD
  const ema12 = recentPrices.slice(-12).reduce((a, b) => a + b, 0) / 12;
  const ema26 = recentPrices.length >= 26 
    ? recentPrices.slice(-26).reduce((a, b) => a + b, 0) / 26 
    : ema12;
  const macd = ema12 - ema26;
  
  // Bollinger Bands
  const std = Math.sqrt(
    recentPrices.reduce((sum, p) => sum + Math.pow(p - avg50, 2), 0) / recentPrices.length
  );
  const bb_upper = avg50 + (2 * std);
  const bb_lower = avg50 - (2 * std);
  
  return {
    rsi: Math.min(100, Math.max(0, rsi)),
    macd,
    bb_upper,
    bb_lower,
    sma_50: avg50,
    sma_200: avg200,
    volume_ma: recentPrices.length > 0 ? recentPrices.length : undefined,
  };
}

// Generate news events
function generateNewsEvents(symbol: string, timestamp: string): NewsEvent[] {
  const newsSources = ['Reuters', 'Bloomberg', 'CNBC', 'WSJ', 'Financial Times'];
  const newsTitles = [
    `${symbol} Reports Strong Earnings`,
    `${symbol} Announces New Product Launch`,
    `Analyst Upgrades ${symbol} Rating`,
    `${symbol} Faces Regulatory Scrutiny`,
    `Market Reacts to ${symbol} News`,
  ];
  
  // Randomly generate 0-2 news events
  const count = Math.floor(Math.random() * 3);
  const events: NewsEvent[] = [];
  
  for (let i = 0; i < count; i++) {
    events.push({
      timestamp,
      title: newsTitles[Math.floor(Math.random() * newsTitles.length)],
      source: newsSources[Math.floor(Math.random() * newsSources.length)],
      sentiment: (Math.random() - 0.5) * 2,
      impact: Math.random() > 0.6 ? 'High' : Math.random() > 0.3 ? 'Medium' : 'Low',
    });
  }
  
  return events;
}

// Generate mock predictions - continuous from past to future
function generatePredictions(
  symbol: string,
  currentPrice: number,
  historicalData: OHLCVDataPoint[]
): PredictionPoint[] {
  const predictions: PredictionPoint[] = [];
  const now = new Date();
  
  // Get price history for indicators
  const priceHistory = historicalData.map(d => d.close);
  
  // Generate predictions for next 24 hours (every 5 minutes = 288 predictions)
  for (let i = 0; i < 288; i++) {
    const timestamp = new Date(now);
    timestamp.setMinutes(timestamp.getMinutes() + i * 5);
    
    // Predict price with trend continuation
    const recentTrend = priceHistory.length >= 2 
      ? (priceHistory[priceHistory.length - 1] - priceHistory[priceHistory.length - 2]) / priceHistory[priceHistory.length - 2]
      : 0;
    const trendFactor = recentTrend * 0.7; // 70% trend continuation
    const randomFactor = (Math.random() - 0.5) * 0.01;
    const change = trendFactor + randomFactor;
    
    const predictedPrice = Math.round(currentPrice * (1 + change * (i + 1) / 288) * 100) / 100;
    const confidence = Math.max(0.5, 0.9 - (i * 0.001)); // Decreasing confidence over time
    
    // Generate technical indicators
    const updatedPriceHistory = [...priceHistory, predictedPrice];
    const technicalIndicators = generateTechnicalIndicators(updatedPriceHistory, predictedPrice);
    
    // Generate trend classification
    const trendSignal: TrendClassification = {
      signal: predictedPrice > currentPrice * 1.01 ? 'BUY' : predictedPrice < currentPrice * 0.99 ? 'SELL' : 'HOLD',
      probabilities: {
        BUY: predictedPrice > currentPrice ? 0.4 + Math.random() * 0.3 : Math.random() * 0.3,
        SELL: predictedPrice < currentPrice ? 0.4 + Math.random() * 0.3 : Math.random() * 0.3,
        HOLD: Math.random() * 0.3 + 0.2,
      },
      confidence: confidence,
      model: 'lightgbm',
    };
    
    // Normalize probabilities
    const total = trendSignal.probabilities.BUY + trendSignal.probabilities.SELL + trendSignal.probabilities.HOLD;
    trendSignal.probabilities.BUY /= total;
    trendSignal.probabilities.SELL /= total;
    trendSignal.probabilities.HOLD /= total;
    
    // Generate sentiment
    const newsEvents = generateNewsEvents(symbol, timestamp.toISOString());
    const avgSentiment = newsEvents.length > 0
      ? newsEvents.reduce((sum, n) => sum + n.sentiment, 0) / newsEvents.length
      : (Math.random() - 0.5) * 0.5;
    
    const sentiment: SentimentData = {
      sentiment_score: avgSentiment,
      sentiment_label: avgSentiment > 0.3 ? 'positive' : avgSentiment < -0.3 ? 'negative' : 'neutral',
      confidence: 0.7 + Math.random() * 0.2,
      news_count: newsEvents.length,
      impact: newsEvents.length > 0 && newsEvents.some(n => n.impact === 'High') ? 'High' : 
              newsEvents.length > 0 ? 'Medium' : 'Low',
    };
    
    // Generate support/resistance levels
    const supportLevels: PriceLevel[] = [
      {
        price: predictedPrice * 0.95,
        strength: Math.floor(Math.random() * 30) + 60,
        type: 'support',
        touches: Math.floor(Math.random() * 5) + 2,
        validated: true,
      },
      {
        price: predictedPrice * 0.92,
        strength: Math.floor(Math.random() * 20) + 50,
        type: 'support',
        touches: Math.floor(Math.random() * 3) + 1,
        validated: true,
      },
    ];
    
    const resistanceLevels: PriceLevel[] = [
      {
        price: predictedPrice * 1.05,
        strength: Math.floor(Math.random() * 30) + 60,
        type: 'resistance',
        touches: Math.floor(Math.random() * 5) + 2,
        validated: true,
      },
      {
        price: predictedPrice * 1.08,
        strength: Math.floor(Math.random() * 20) + 50,
        type: 'resistance',
        touches: Math.floor(Math.random() * 3) + 1,
        validated: true,
      },
    ];
    
    // Timing score (0-1, higher = better entry/exit timing)
    const timingScore = 0.5 + (trendSignal.probabilities.BUY - trendSignal.probabilities.SELL) * 0.3 + Math.random() * 0.2;
    
    // Volatility
    const recentPrices = priceHistory.slice(-20);
    const volatility = recentPrices.length > 1
      ? Math.sqrt(recentPrices.reduce((sum, p, i) => {
          if (i === 0) return sum;
          const change = (p - recentPrices[i - 1]) / recentPrices[i - 1];
          return sum + change * change;
        }, 0) / (recentPrices.length - 1))
      : 0.02;
    
    predictions.push({
      timestamp: timestamp.toISOString(),
      predicted_price: predictedPrice,
      confidence,
      upper_bound: predictedPrice * (1 + volatility * 2),
      lower_bound: predictedPrice * (1 - volatility * 2),
      trend: trendSignal,
      sentiment,
      support_levels: supportLevels,
      resistance_levels: resistanceLevels,
      fused_signal: trendSignal.signal,
      fused_confidence: confidence * 0.8 + sentiment.confidence * 0.2,
      technical_indicators: technicalIndicators,
      news_events: newsEvents,
      timing_score: Math.max(0, Math.min(1, timingScore)),
      volatility,
    });
    
    // Update current price for next iteration
    currentPrice = predictedPrice;
  }
  
  return predictions;
}

// Base prices for each stock
const BASE_PRICES: Record<string, number> = {
  // Technology
  AAPL: 180,
  MSFT: 380,
  GOOGL: 140,
  GOOG: 142,
  AMZN: 150,
  META: 350,
  NVDA: 500,
  TSLA: 250,
  NFLX: 480,
  INTC: 45,
  // Energy
  XOM: 105,
  CVX: 150,
  SLB: 52,
  COP: 115,
  EOG: 125,
  // Healthcare
  JNJ: 160,
  PFE: 30,
  UNH: 520,
  ABBV: 165,
  TMO: 550,
  // Finance
  JPM: 175,
  BAC: 35,
  GS: 380,
  MS: 95,
  WFC: 55,
  'BRK.B': 360,
  V: 250,
  // Consumer
  WMT: 165,
  PG: 155,
  KO: 60,
  PEP: 175,
  MCD: 290,
};

export function generateMockStockData(symbol: string): StockData {
  const basePrice = BASE_PRICES[symbol] || 100;
  const priceChange = (Math.random() - 0.5) * 5;
  const priceChangePercent = (priceChange / basePrice) * 100;
  const currentPrice = Math.round((basePrice + priceChange) * 100) / 100;
  
  const historicalData = generateHistoricalData(symbol, basePrice);
  const predictions = generatePredictions(symbol, currentPrice, historicalData);
  
  // Get latest support/resistance from predictions
  const latestPrediction = predictions[0];
  
  return {
    symbol,
    name: SP500_STOCKS.find(s => s.symbol === symbol)?.name || symbol,
    current_price: currentPrice,
    price_change: priceChange,
    price_change_percent: priceChangePercent,
    historical_data: historicalData,
    predictions,
    support_levels: latestPrediction.support_levels,
    resistance_levels: latestPrediction.resistance_levels,
    last_updated: new Date().toISOString(),
  };
}

export function getAllMockStocks(): StockData[] {
  return SP500_STOCKS.map(stock => generateMockStockData(stock.symbol));
}
