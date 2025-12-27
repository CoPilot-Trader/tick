'use client';

import { TrendingUp, TrendingDown, BarChart3, Activity, Clock } from 'lucide-react';
import { StockData } from '@/types';

interface StockOverviewProps {
  data: StockData;
}

export default function StockOverview({ data }: StockOverviewProps) {
  const isPositive = data.price_change >= 0;
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;
  const latestPrediction = data.predictions[0];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-lg font-bold text-white">{data.symbol}</h2>
            <p className="text-xs text-gray-400">{data.name}</p>
          </div>
          <div className="border-l border-gray-800 pl-4">
            <p className="text-xl font-bold text-white">
              ${data.current_price.toFixed(2)}
            </p>
            <div className={`flex items-center gap-1 text-xs ${isPositive ? 'text-success-400' : 'text-danger-400'}`}>
              <TrendIcon className="w-3 h-3" />
              <span className="font-semibold">
                {isPositive ? '+' : ''}{data.price_change.toFixed(2)} ({isPositive ? '+' : ''}
                {data.price_change_percent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <BarChart3 className="w-3 h-3 text-gray-400" />
            <span className="text-xs text-gray-400">Support:</span>
            <span className="text-sm font-semibold text-white">{data.support_levels.length}</span>
          </div>

          <div className="flex items-center gap-1.5">
            <BarChart3 className="w-3 h-3 text-gray-400" />
            <span className="text-xs text-gray-400">Resistance:</span>
            <span className="text-sm font-semibold text-white">{data.resistance_levels.length}</span>
          </div>

          <div className="flex items-center gap-1.5">
            <Activity className="w-3 h-3 text-gray-400" />
            <span className="text-xs text-gray-400">Predictions:</span>
            <span className="text-sm font-semibold text-white">{data.predictions.length}</span>
          </div>

          {latestPrediction && (
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-gray-400" />
              <span className="text-xs text-gray-400">Timing:</span>
              <span className="text-sm font-semibold text-white">
                {(latestPrediction.timing_score || 0) * 100}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
