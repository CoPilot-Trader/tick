'use client';

import { X, TrendingUp, TrendingDown, Minus, BarChart3, MessageSquare, Target } from 'lucide-react';
import { PredictionPoint } from '@/types';
import { format } from 'date-fns';

interface PredictionDetailProps {
  prediction: PredictionPoint | null;
  onClose: () => void;
}

export default function PredictionDetail({ prediction, onClose }: PredictionDetailProps) {
  if (!prediction) return null;

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return 'text-success-400 bg-success-950 border-success-800';
      case 'SELL':
        return 'text-danger-400 bg-danger-950 border-danger-800';
      default:
        return 'text-gray-400 bg-gray-800 border-gray-700';
    }
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return 'text-success-400';
    if (score < -0.3) return 'text-danger-400';
    return 'text-gray-400';
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'High':
        return 'text-danger-400 bg-danger-950';
      case 'Medium':
        return 'text-yellow-400 bg-yellow-950';
      default:
        return 'text-gray-400 bg-gray-800';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70">
      <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">
            Prediction Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Timestamp */}
          <div>
            <p className="text-sm text-gray-400">Time</p>
            <p className="text-lg font-semibold text-white">
              {format(new Date(prediction.timestamp), 'PPpp')}
            </p>
          </div>

          {/* Price Prediction */}
          <div className="bg-blue-950 rounded-lg p-4 border border-blue-800">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-blue-300">Price Prediction</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-blue-400">Predicted Price</p>
                <p className="text-2xl font-bold text-white">
                  ${prediction.predicted_price.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-blue-400">Confidence</p>
                <p className="text-2xl font-bold text-white">
                  {(prediction.confidence * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-blue-400">Upper Bound</p>
                <p className="text-lg font-semibold text-white">
                  ${prediction.upper_bound.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-blue-400">Lower Bound</p>
                <p className="text-lg font-semibold text-white">
                  ${prediction.lower_bound.toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Trend Classification */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5 text-gray-400" />
              <h3 className="font-semibold text-white">Trend Classification</h3>
            </div>
            <div className="space-y-3">
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${getSignalColor(prediction.trend.signal)}`}>
                {prediction.trend.signal === 'BUY' && <TrendingUp className="w-5 h-5" />}
                {prediction.trend.signal === 'SELL' && <TrendingDown className="w-5 h-5" />}
                {prediction.trend.signal === 'HOLD' && <Minus className="w-5 h-5" />}
                <span className="font-semibold">{prediction.trend.signal}</span>
                <span className="text-sm">({(prediction.trend.confidence * 100).toFixed(1)}% confidence)</span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-gray-900 rounded border border-gray-700">
                  <p className="text-xs text-gray-400">BUY</p>
                  <p className="font-semibold text-white">
                    {(prediction.trend.probabilities.BUY * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="text-center p-2 bg-gray-900 rounded border border-gray-700">
                  <p className="text-xs text-gray-400">HOLD</p>
                  <p className="font-semibold text-white">
                    {(prediction.trend.probabilities.HOLD * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="text-center p-2 bg-gray-900 rounded border border-gray-700">
                  <p className="text-xs text-gray-400">SELL</p>
                  <p className="font-semibold text-white">
                    {(prediction.trend.probabilities.SELL * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* News Sentiment */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="w-5 h-5 text-gray-400" />
              <h3 className="font-semibold text-white">News Sentiment</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Sentiment Score</span>
                <span className={`font-semibold ${getSentimentColor(prediction.sentiment.sentiment_score)}`}>
                  {prediction.sentiment.sentiment_score > 0 ? '+' : ''}
                  {prediction.sentiment.sentiment_score.toFixed(3)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Label</span>
                <span className="font-semibold text-white capitalize">
                  {prediction.sentiment.sentiment_label}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Confidence</span>
                <span className="font-semibold text-white">
                  {(prediction.sentiment.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">News Count</span>
                <span className="font-semibold text-white">
                  {prediction.sentiment.news_count} articles
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Impact</span>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${getImpactColor(prediction.sentiment.impact)}`}>
                  {prediction.sentiment.impact}
                </span>
              </div>
              
              {/* News Events */}
              {prediction.news_events && prediction.news_events.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-700">
                  <p className="text-xs font-semibold text-gray-400 mb-2">Recent News Events</p>
                  <div className="space-y-2">
                    {prediction.news_events.map((news, index) => (
                      <div key={index} className="bg-gray-900 rounded p-2 border border-gray-700">
                        <p className="text-xs font-semibold text-white mb-1">{news.title}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">{news.source}</span>
                          <span className={`text-xs px-2 py-0.5 rounded ${getImpactColor(news.impact)}`}>
                            {news.impact}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Technical Indicators */}
          {prediction.technical_indicators && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-5 h-5 text-gray-400" />
                <h3 className="font-semibold text-white">Technical Indicators</h3>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {prediction.technical_indicators.rsi !== undefined && (
                  <div>
                    <p className="text-xs text-gray-400">RSI</p>
                    <p className="text-sm font-semibold text-white">
                      {prediction.technical_indicators.rsi.toFixed(2)}
                    </p>
                  </div>
                )}
                {prediction.technical_indicators.macd !== undefined && (
                  <div>
                    <p className="text-xs text-gray-400">MACD</p>
                    <p className="text-sm font-semibold text-white">
                      {prediction.technical_indicators.macd.toFixed(2)}
                    </p>
                  </div>
                )}
                {prediction.technical_indicators.sma_50 !== undefined && (
                  <div>
                    <p className="text-xs text-gray-400">SMA 50</p>
                    <p className="text-sm font-semibold text-white">
                      ${prediction.technical_indicators.sma_50.toFixed(2)}
                    </p>
                  </div>
                )}
                {prediction.technical_indicators.sma_200 !== undefined && (
                  <div>
                    <p className="text-xs text-gray-400">SMA 200</p>
                    <p className="text-sm font-semibold text-white">
                      ${prediction.technical_indicators.sma_200.toFixed(2)}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Timing Score */}
          {prediction.timing_score !== undefined && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white mb-1">Timing Score</p>
                  <p className="text-xs text-gray-400">Entry/Exit timing quality</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">
                    {(prediction.timing_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Support/Resistance Levels */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-5 h-5 text-gray-400" />
              <h3 className="font-semibold text-white">Support & Resistance Levels</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-semibold text-success-400 mb-2">Support Levels</p>
                <div className="space-y-2">
                  {prediction.support_levels.map((level, index) => (
                    <div key={index} className="bg-gray-900 rounded p-2 border border-success-800">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-white">
                          ${level.price.toFixed(2)}
                        </span>
                        <span className="text-xs text-gray-400">
                          Strength: {level.strength}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-400">
                        {level.touches} touches • {level.validated ? 'Validated' : 'Pending'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-danger-400 mb-2">Resistance Levels</p>
                <div className="space-y-2">
                  {prediction.resistance_levels.map((level, index) => (
                    <div key={index} className="bg-gray-900 rounded p-2 border border-danger-800">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-white">
                          ${level.price.toFixed(2)}
                        </span>
                        <span className="text-xs text-gray-400">
                          Strength: {level.strength}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-400">
                        {level.touches} touches • {level.validated ? 'Validated' : 'Pending'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Fused Signal */}
          <div className={`rounded-lg p-4 border ${getSignalColor(prediction.fused_signal)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-1">Fused Trading Signal</p>
                <div className="flex items-center gap-2">
                  {prediction.fused_signal === 'BUY' && <TrendingUp className="w-6 h-6" />}
                  {prediction.fused_signal === 'SELL' && <TrendingDown className="w-6 h-6" />}
                  {prediction.fused_signal === 'HOLD' && <Minus className="w-6 h-6" />}
                  <span className="text-2xl font-bold">{prediction.fused_signal}</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400 mb-1">Confidence</p>
                <p className="text-2xl font-bold text-white">
                  {(prediction.fused_confidence * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

