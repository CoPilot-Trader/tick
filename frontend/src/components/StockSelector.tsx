'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { SP500_STOCKS } from '@/lib/mockData';

interface StockSelectorProps {
  selectedStock: string;
  onStockChange: (symbol: string) => void;
}

export default function StockSelector({ selectedStock, onStockChange }: StockSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedStockName = SP500_STOCKS.find(s => s.symbol === selectedStock)?.name || selectedStock;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-2 text-left bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-750 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
      >
        <div>
          <div className="font-semibold text-white">{selectedStock}</div>
          <div className="text-xs text-gray-400">{selectedStockName}</div>
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-60 overflow-auto">
            {SP500_STOCKS.map((stock) => (
              <button
                key={stock.symbol}
                onClick={() => {
                  onStockChange(stock.symbol);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-2 text-left hover:bg-gray-750 transition-colors ${
                  selectedStock === stock.symbol ? 'bg-gray-750' : ''
                }`}
              >
                <div className="font-semibold text-white">{stock.symbol}</div>
                <div className="text-xs text-gray-400">{stock.name}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
