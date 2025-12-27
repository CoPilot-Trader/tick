'use client';

import { useState, useEffect } from 'react';
import { StockData, PredictionPoint, GraphFilters } from '@/types';
import { apiClient } from '@/lib/api/client';
import MultiStockSelector from '@/components/MultiStockSelector';
import StockOverview from '@/components/StockOverview';
import ModernPriceChart from '@/components/ModernPriceChart';
import ComparisonChart from '@/components/ComparisonChart';
import PredictionDetail from '@/components/PredictionDetail';

const defaultFilters: GraphFilters = {
  showActualPrice: true,
  showPredictedPrice: true,
  showSupportResistance: false, // Disabled in comparison mode
  showConfidenceBounds: false,
  showVolume: false,
  showRSI: false,
  showMACD: false,
  showBollingerBands: false,
  showMovingAverages: false,
  showNewsEvents: true,
  showTimingSignals: false,
};

export default function Home() {
  const [selectedStocks, setSelectedStocks] = useState<string[]>(['AAPL']);
  const [stocksData, setStocksData] = useState<StockData[]>([]);
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionPoint | null>(null);
  const [filters, setFilters] = useState<GraphFilters>(defaultFilters);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStocksData = async () => {
      setLoading(true);
      try {
        const data = await Promise.all(
          selectedStocks.map(symbol => apiClient.getStockData(symbol))
        );
        setStocksData(data);
      } catch (error) {
        console.error('Error loading stock data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (selectedStocks.length > 0) {
      loadStocksData();
    }
  }, [selectedStocks]);

  if (loading || stocksData.length === 0) {
    return (
      <div className="h-screen w-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading stock data...</p>
        </div>
      </div>
    );
  }

  const isComparisonMode = selectedStocks.length > 1;
  const primaryStock = stocksData[0];

  return (
    <div className="h-screen w-screen bg-gray-950 overflow-hidden flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-2 flex-shrink-0">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-shrink-0">
            <h1 className="text-lg font-bold text-white">TICK</h1>
            <p className="text-xs text-gray-400 hidden sm:block">Time-Indexed Composite Knowledge for Markets</p>
          </div>
          <div className="flex-1 max-w-2xl min-w-0">
            <MultiStockSelector
              selectedStocks={selectedStocks}
              onStocksChange={setSelectedStocks}
              maxStocks={5}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden grid grid-rows-[auto_1fr] gap-4 p-4">
        {/* Stock Overview - Show primary stock or compact comparison summary */}
        <div className="flex-shrink-0">
          {isComparisonMode ? (
            <div className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-2">
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400 font-medium">Comparison:</span>
                {stocksData.map((stock, index) => {
                  const isPositive = stock.price_change >= 0;
                  const isBestPerformer = stocksData.every(
                    s => s === stock || stock.price_change_percent >= s.price_change_percent
                  );
                  return (
                    <div 
                      key={stock.symbol} 
                      className={`flex items-center gap-1.5 px-2 py-1 rounded ${
                        isBestPerformer ? 'bg-primary-500/20 border border-primary-500/50' : 'bg-gray-800'
                      }`}
                    >
                      <div
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444'][index % 5] }}
                      />
                      <span className="text-xs font-semibold text-white">{stock.symbol}</span>
                      <span className="text-xs text-gray-400">
                        ${stock.current_price.toFixed(2)}
                      </span>
                      <span className={`text-xs font-semibold ${isPositive ? 'text-success-400' : 'text-danger-400'}`}>
                        {isPositive ? '+' : ''}{stock.price_change_percent.toFixed(2)}%
                      </span>
                      {isBestPerformer && (
                        <span className="text-xs text-primary-400 font-bold">★</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <StockOverview data={primaryStock} />
          )}
        </div>

        {/* Chart - Comparison or Single Stock */}
        <div className="flex-1 min-h-0">
          {isComparisonMode ? (
            <ComparisonChart
              stocksData={stocksData}
              selectedPrediction={selectedPrediction}
              onPredictionClick={setSelectedPrediction}
              filters={filters}
              onFilterChange={setFilters}
            />
          ) : (
            <ModernPriceChart
              data={primaryStock}
              selectedPrediction={selectedPrediction}
              onPredictionClick={setSelectedPrediction}
              filters={filters}
              onFilterChange={setFilters}
            />
          )}
        </div>
      </main>

      {/* Prediction Detail Modal */}
      {selectedPrediction && (
        <PredictionDetail
          prediction={selectedPrediction}
          onClose={() => setSelectedPrediction(null)}
        />
      )}
    </div>
  );
}
