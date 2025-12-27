'use client';

import { useState } from 'react';
import { X, ChevronDown } from 'lucide-react';
import { SP500_STOCKS } from '@/lib/mockData';

interface MultiStockSelectorProps {
  selectedStocks: string[];
  onStocksChange: (symbols: string[]) => void;
  maxStocks?: number;
}

export default function MultiStockSelector({ 
  selectedStocks, 
  onStocksChange,
  maxStocks = 5 
}: MultiStockSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleStock = (symbol: string) => {
    if (selectedStocks.includes(symbol)) {
      onStocksChange(selectedStocks.filter(s => s !== symbol));
    } else {
      if (selectedStocks.length < maxStocks) {
        onStocksChange([...selectedStocks, symbol]);
      }
    }
  };

  const removeStock = (symbol: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onStocksChange(selectedStocks.filter(s => s !== symbol));
  };

  const availableStocks = SP500_STOCKS.filter(
    stock => !selectedStocks.includes(stock.symbol)
  );

  return (
    <div className="relative">
      {/* Selected Stocks Display */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 w-full px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-750 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors cursor-pointer min-h-[36px]"
      >
        <div className="flex-1 flex items-center gap-1.5 flex-wrap min-w-0">
          {selectedStocks.length === 0 ? (
            <span className="text-gray-400 text-xs">Select stocks...</span>
          ) : (
            selectedStocks.map((symbol) => {
              const stock = SP500_STOCKS.find(s => s.symbol === symbol);
              return (
                <div
                  key={symbol}
                  className="flex items-center gap-1 px-1.5 py-0.5 bg-primary-600 text-white rounded text-xs font-medium flex-shrink-0"
                >
                  <span>{symbol}</span>
                  <button
                    onClick={(e) => removeStock(symbol, e)}
                    className="hover:bg-primary-700 rounded p-0.5 transition-colors flex-shrink-0"
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {/* Dropdown */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-60 overflow-auto">
            {availableStocks.length === 0 ? (
              <div className="px-4 py-2 text-sm text-gray-400">
                All stocks selected (max {maxStocks})
              </div>
            ) : (
              availableStocks.map((stock) => (
                <button
                  key={stock.symbol}
                  onClick={() => {
                    toggleStock(stock.symbol);
                    if (selectedStocks.length + 1 >= maxStocks) {
                      setIsOpen(false);
                    }
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-gray-750 transition-colors"
                >
                  <div className="font-semibold text-white">{stock.symbol}</div>
                  <div className="text-xs text-gray-400">{stock.name}</div>
                </button>
              ))
            )}
          </div>
        </>
      )}

      {/* Max stocks warning */}
      {selectedStocks.length >= maxStocks && (
        <p className="text-xs text-amber-400 mt-0.5">
          Max {maxStocks} stocks
        </p>
      )}
    </div>
  );
}

