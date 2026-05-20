'use client';

import { StockData } from '@/types';
import MiniChart from './MiniChart';

interface ComparisonGridProps {
  stocks: StockData[];
  activeIndex: number;
  onSelect: (index: number) => void;
}

/**
 * Multi-ticker comparison grid — shows up to 4 tickers' charts side-by-side
 * (2x2). Clicking a cell selects that ticker (parent can switch to single view).
 */
export default function ComparisonGrid({ stocks, activeIndex, onSelect }: ComparisonGridProps) {
  const shown = stocks.slice(0, 4);
  // 1 → 1 col, 2 → 2 cols, 3-4 → 2 cols (2 rows)
  const cols = shown.length === 1 ? 1 : 2;

  return (
    <div
      className="w-full h-full p-2"
      style={{
        background: '#0d0f15',
        display: 'grid',
        gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
        gridAutoRows: '1fr',
        gap: 8,
      }}
    >
      {shown.map((stock, i) => (
        <MiniChart
          key={stock.symbol}
          data={stock}
          active={i === activeIndex}
          onClick={() => onSelect(i)}
        />
      ))}
    </div>
  );
}
