'use client';

import { GraphFilters as GraphFiltersType } from '@/types';

interface GraphFiltersProps {
  filters: GraphFiltersType;
  onFilterChange: (filters: GraphFiltersType) => void;
}

export default function GraphFilters({ filters, onFilterChange }: GraphFiltersProps) {
  const updateFilter = (key: keyof GraphFiltersType, value: boolean) => {
    onFilterChange({ ...filters, [key]: value });
  };

  const filterButtons = [
    { key: 'showActualPrice' as const, label: 'Actual Price', group: 'price' },
    { key: 'showPredictedPrice' as const, label: 'Predicted', group: 'price' },
    { key: 'showConfidenceBounds' as const, label: 'Bounds', group: 'price' },
    { key: 'showSupportResistance' as const, label: 'S/R Levels', group: 'levels' },
    { key: 'showMovingAverages' as const, label: 'MA', group: 'levels' },
    { key: 'showBollingerBands' as const, label: 'BB', group: 'levels' },
    { key: 'showRSI' as const, label: 'RSI', group: 'technical' },
    { key: 'showMACD' as const, label: 'MACD', group: 'technical' },
    { key: 'showVolume' as const, label: 'Volume', group: 'technical' },
    { key: 'showNewsEvents' as const, label: 'News', group: 'events' },
    { key: 'showTimingSignals' as const, label: 'Timing', group: 'events' },
  ];

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {filterButtons.map((filter) => (
        <button
          key={filter.key}
          onClick={() => updateFilter(filter.key, !filters[filter.key])}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
            filters[filter.key]
              ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/20'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-750 hover:text-gray-300 border border-gray-700'
          }`}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}
