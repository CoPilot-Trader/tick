'use client';

import React, { useMemo, useState, useRef, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Dot,
  Area,
  ComposedChart,
  Brush,
} from 'recharts';
import { StockData, PredictionPoint, GraphFilters, OHLCVDataPoint } from '@/types';
import { format } from 'date-fns';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import GraphFiltersComponent from './GraphFilters';

interface ComparisonChartProps {
  stocksData: StockData[];
  selectedPrediction: PredictionPoint | null;
  onPredictionClick: (prediction: PredictionPoint | null) => void;
  filters: GraphFilters;
  onFilterChange: (filters: GraphFilters) => void;
}

interface ChartDataPoint {
  timestamp: string;
  time: string;
  [key: string]: any; // Dynamic keys for each stock
}

// Color palette for multiple stocks
const STOCK_COLORS = [
  '#3b82f6', // Blue
  '#8b5cf6', // Purple
  '#22c55e', // Green
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316', // Orange
  '#6366f1', // Indigo
];

interface SelectionBox {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export default function ComparisonChart({
  stocksData,
  selectedPrediction,
  onPredictionClick,
  filters,
  onFilterChange,
}: ComparisonChartProps) {
  const [zoomStart, setZoomStart] = useState<number | null>(null);
  const [zoomEnd, setZoomEnd] = useState<number | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionBox, setSelectionBox] = useState<SelectionBox | null>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);

  // Normalize all stocks to same time range and create comparison data
  const chartData = useMemo(() => {
    if (stocksData.length === 0) return [];

    // Use the first stock's timeline as the base (they should all have similar timelines)
    const baseStock = stocksData[0];
    const allDataPoints: ChartDataPoint[] = [];

    // Combine historical and predictions for timeline
    const now = new Date();
    const historicalEnd = baseStock.historical_data[baseStock.historical_data.length - 1];
    
    // Create points from historical data (sample every 3rd point for better coverage)
    const filteredHistorical = baseStock.historical_data.filter((_, i) => i % 3 === 0 || i === baseStock.historical_data.length - 1);
    
    filteredHistorical.forEach((point) => {
      const chartPoint: ChartDataPoint = {
        timestamp: point.timestamp,
        time: format(new Date(point.timestamp), 'HH:mm'),
      };

      // Add actual prices for all stocks at this timestamp
      stocksData.forEach((stock, stockIndex) => {
        const color = STOCK_COLORS[stockIndex % STOCK_COLORS.length];
        const symbol = stock.symbol;
        
        // Try exact timestamp match first
        let matchingPoint = stock.historical_data.find(h => h.timestamp === point.timestamp);
        
        // If no exact match, find closest by timestamp (within 5 minutes)
        if (!matchingPoint) {
          const pointTime = new Date(point.timestamp).getTime();
          matchingPoint = stock.historical_data.reduce((closest, current) => {
            if (!closest) return current;
            const closestDiff = Math.abs(new Date(closest.timestamp).getTime() - pointTime);
            const currentDiff = Math.abs(new Date(current.timestamp).getTime() - pointTime);
            return currentDiff < closestDiff && currentDiff < 5 * 60 * 1000 ? current : closest;
          }, null as OHLCVDataPoint | null);
        }
        
        if (matchingPoint) {
          chartPoint[`${symbol}_actual`] = matchingPoint.close;
          chartPoint[`${symbol}_color`] = color;
        }
      });

      allDataPoints.push(chartPoint);
    });

    // Add transition point (last actual to first prediction)
    if (historicalEnd && baseStock.predictions.length > 0) {
      const transitionPoint: ChartDataPoint = {
        timestamp: now.toISOString(),
        time: format(now, 'HH:mm'),
      };

      stocksData.forEach((stock, stockIndex) => {
        const color = STOCK_COLORS[stockIndex % STOCK_COLORS.length];
        const symbol = stock.symbol;
        const lastHistorical = stock.historical_data[stock.historical_data.length - 1];
        const firstPrediction = stock.predictions[0];
        
        if (lastHistorical) {
          transitionPoint[`${symbol}_actual`] = lastHistorical.close;
        }
        if (firstPrediction) {
          transitionPoint[`${symbol}_predicted`] = firstPrediction.predicted_price;
        }
        transitionPoint[`${symbol}_color`] = color;
      });

      allDataPoints.push(transitionPoint);
    }

    // Add prediction points (sample every 3rd for better coverage)
    const filteredPredictions = baseStock.predictions.filter((_, i) => i % 3 === 0);
    
    filteredPredictions.forEach((prediction) => {
      const chartPoint: ChartDataPoint = {
        timestamp: prediction.timestamp,
        time: format(new Date(prediction.timestamp), 'HH:mm'),
      };

      // Add predicted prices for all stocks at this timestamp
      stocksData.forEach((stock, stockIndex) => {
        const color = STOCK_COLORS[stockIndex % STOCK_COLORS.length];
        const symbol = stock.symbol;
        
        // Try exact timestamp match first
        let matchingPrediction = stock.predictions.find(p => p.timestamp === prediction.timestamp);
        
        // If no exact match, find closest by timestamp (within 5 minutes)
        if (!matchingPrediction) {
          const predTime = new Date(prediction.timestamp).getTime();
          matchingPrediction = stock.predictions.reduce((closest, current) => {
            if (!closest) return current;
            const closestDiff = Math.abs(new Date(closest.timestamp).getTime() - predTime);
            const currentDiff = Math.abs(new Date(current.timestamp).getTime() - predTime);
            return currentDiff < closestDiff && currentDiff < 5 * 60 * 1000 ? current : closest;
          }, null as PredictionPoint | null);
        }
        
        if (matchingPrediction) {
          chartPoint[`${symbol}_predicted`] = matchingPrediction.predicted_price;
          chartPoint[`${symbol}_color`] = color;
          chartPoint[`${symbol}_prediction`] = matchingPrediction;
        }
      });

      allDataPoints.push(chartPoint);
    });

    // Sort by timestamp
    allDataPoints.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // Debug: Log first few points
    if (allDataPoints.length > 0) {
      const samplePoint = allDataPoints[0];
      const dataKeys = Object.keys(samplePoint).filter(k => !['timestamp', 'time'].includes(k));
      const sampleDataValues = stocksData.map(s => ({
        symbol: s.symbol,
        actual: samplePoint[`${s.symbol}_actual`],
        predicted: samplePoint[`${s.symbol}_predicted`],
      }));
      
      // Count data points per stock
      const stockDataCounts = stocksData.map(s => {
        const actualCount = allDataPoints.filter(p => {
          const val = p[`${s.symbol}_actual`];
          return val !== null && val !== undefined && !isNaN(val);
        }).length;
        const predictedCount = allDataPoints.filter(p => {
          const val = p[`${s.symbol}_predicted`];
          return val !== null && val !== undefined && !isNaN(val);
        }).length;
        return {
          symbol: s.symbol,
          actualCount,
          predictedCount,
          totalCount: actualCount + predictedCount,
        };
      });
      
      console.log('Comparison chart data:', {
        totalPoints: allDataPoints.length,
        firstPoint: samplePoint,
        dataKeys: dataKeys,
        stocks: stocksData.map(s => s.symbol),
        sampleDataValues: sampleDataValues,
        stockDataCounts: stockDataCounts,
        hasData: allDataPoints.some(p => {
          return stocksData.some(s => {
            const actual = p[`${s.symbol}_actual`];
            const predicted = p[`${s.symbol}_predicted`];
            return (actual !== null && actual !== undefined && !isNaN(actual)) ||
                   (predicted !== null && predicted !== undefined && !isNaN(predicted));
          });
        }),
      });
    }

    return allDataPoints;
  }, [stocksData]);

  // Apply zoom if set
  const displayedData = useMemo(() => {
    if (zoomStart === null || zoomEnd === null) return chartData;
    return chartData.slice(zoomStart, zoomEnd + 1);
  }, [chartData, zoomStart, zoomEnd]);

  // Mouse event handlers for selection box
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    const rect = chartContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setIsSelecting(true);
    setSelectionBox({
      startX: x,
      startY: y,
      endX: x,
      endY: y,
    });
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!isSelecting || !selectionBox) return;
    const rect = chartContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setSelectionBox({
      ...selectionBox,
      endX: x,
      endY: y,
    });
  }, [isSelecting, selectionBox]);

  const handleMouseUp = useCallback(() => {
    if (!isSelecting || !selectionBox) return;

    const rect = chartContainerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const minX = Math.min(selectionBox.startX, selectionBox.endX);
    const maxX = Math.max(selectionBox.startX, selectionBox.endX);

    if (maxX - minX > 50) {
      const containerPadding = 16;
      const leftMargin = 60;
      const rightMargin = 20;
      
      const chartAreaLeft = containerPadding + leftMargin;
      const chartAreaRight = rect.width - containerPadding - rightMargin;
      const chartAreaWidth = chartAreaRight - chartAreaLeft;
      
      const relativeMinX = Math.max(0, minX - chartAreaLeft);
      const relativeMaxX = Math.min(chartAreaWidth, maxX - chartAreaLeft);

      const startIndex = Math.floor((relativeMinX / chartAreaWidth) * chartData.length);
      const endIndex = Math.ceil((relativeMaxX / chartAreaWidth) * chartData.length);

      const validStart = Math.max(0, Math.min(startIndex, chartData.length - 1));
      const validEnd = Math.max(validStart + 1, Math.min(endIndex, chartData.length));

      if (validStart < validEnd) {
        setZoomStart(validStart);
        setZoomEnd(validEnd - 1);
      }
    }

    setIsSelecting(false);
    setSelectionBox(null);
  }, [isSelecting, selectionBox, chartData.length]);

  const handleZoomIn = () => {
    if (zoomStart === null || zoomEnd === null) {
      const start = Math.floor(chartData.length * 0.25);
      const end = Math.floor(chartData.length * 0.75);
      setZoomStart(start);
      setZoomEnd(end);
    } else {
      const range = zoomEnd - zoomStart;
      const newRange = Math.floor(range * 0.8);
      const center = Math.floor((zoomStart + zoomEnd) / 2);
      const newStart = Math.max(0, center - Math.floor(newRange / 2));
      const newEnd = Math.min(chartData.length - 1, newStart + newRange);
      setZoomStart(newStart);
      setZoomEnd(newEnd);
    }
  };

  const handleZoomOut = () => {
    if (zoomStart === null || zoomEnd === null) return;
    
    const range = zoomEnd - zoomStart;
    const newRange = Math.floor(range * 1.2);
    const center = Math.floor((zoomStart + zoomEnd) / 2);
    const newStart = Math.max(0, center - Math.floor(newRange / 2));
    const newEnd = Math.min(chartData.length - 1, newStart + newRange);
    
    if (newStart === 0 && newEnd === chartData.length - 1) {
      setZoomStart(null);
      setZoomEnd(null);
    } else {
      setZoomStart(newStart);
      setZoomEnd(newEnd);
    }
  };

  const handleResetZoom = () => {
    setZoomStart(null);
    setZoomEnd(null);
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">{payload[0]?.payload?.time}</p>
        {payload.map((entry: any, index: number) => {
          const dataKey = entry.dataKey as string;
          const symbol = dataKey.replace('_actual', '').replace('_predicted', '');
          const isPredicted = dataKey.includes('_predicted');
          const value = entry.value;
          
          if (value === null || value === undefined) return null;
          
          return (
            <p key={index} className="text-sm font-semibold" style={{ color: entry.color }}>
              {symbol}: ${value.toFixed(2)} {isPredicted && '(Predicted)'}
            </p>
          );
        })}
      </div>
    );
  };

  const selectionStyle = selectionBox ? {
    left: `${Math.min(selectionBox.startX, selectionBox.endX)}px`,
    top: `${Math.min(selectionBox.startY, selectionBox.endY)}px`,
    width: `${Math.abs(selectionBox.endX - selectionBox.startX)}px`,
    height: `${Math.abs(selectionBox.endY - selectionBox.startY)}px`,
  } : {};

  // Calculate price range for all stocks
  const priceRange = useMemo(() => {
    if (chartData.length === 0) return { min: 0, max: 100 };
    
    let min = Infinity;
    let max = -Infinity;

    chartData.forEach(point => {
      stocksData.forEach(stock => {
        const actual = point[`${stock.symbol}_actual`];
        const predicted = point[`${stock.symbol}_predicted`];
        if (actual !== null && actual !== undefined && !isNaN(actual) && actual > 0) {
          min = Math.min(min, actual);
          max = Math.max(max, actual);
        }
        if (predicted !== null && predicted !== undefined && !isNaN(predicted) && predicted > 0) {
          min = Math.min(min, predicted);
          max = Math.max(max, predicted);
        }
      });
    });

    const range = { 
      min: min === Infinity ? 0 : Math.max(0, min * 0.98), 
      max: max === -Infinity ? 100 : max * 1.02 
    };
    
    console.log('Price range calculated:', range, 'from', chartData.length, 'points');
    
    return range;
  }, [chartData, stocksData]);

  return (
    <div 
      ref={chartContainerRef}
      className="w-full h-full bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col relative"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ userSelect: 'none', cursor: isSelecting ? 'crosshair' : 'default' }}
    >
      {/* Selection Box Overlay */}
      {selectionBox && (
        <div
          className="absolute border-2 border-primary-500 bg-primary-500/20 pointer-events-none z-10 rounded"
          style={selectionStyle}
        />
      )}

      {/* Header */}
      <div className="mb-3 flex items-center justify-between z-20 relative">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-sm font-semibold text-white">
              Stock Comparison ({stocksData.length} stocks)
            </h3>
            <span className="text-xs text-gray-400">
              {zoomStart !== null && zoomEnd !== null
                ? `${displayedData.length} points (zoomed)`
                : `${chartData.length} points`}
            </span>
            <span className="text-xs text-gray-500">
              {isSelecting ? 'Release to zoom' : 'Click and drag on chart to zoom'}
            </span>
          </div>
          <GraphFiltersComponent filters={filters} onFilterChange={onFilterChange} />
          
          {/* Stock Legend with Performance */}
          <div className="flex items-center gap-4 mt-2 flex-wrap">
            {stocksData.map((stock, index) => {
              const isPositive = stock.price_change >= 0;
              const isBestPerformer = stocksData.every(
                s => s === stock || stock.price_change_percent >= s.price_change_percent
              );
              return (
                <div 
                  key={stock.symbol} 
                  className={`flex items-center gap-2 px-2 py-1 rounded ${
                    isBestPerformer ? 'bg-primary-500/20 border border-primary-500/50' : ''
                  }`}
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: STOCK_COLORS[index % STOCK_COLORS.length] }}
                  />
                  <span className="text-xs text-gray-300 font-medium">{stock.symbol}</span>
                  <span className="text-xs text-gray-500">
                    ${stock.current_price.toFixed(2)}
                  </span>
                  <span className={`text-xs font-semibold ${isPositive ? 'text-success-400' : 'text-danger-400'}`}>
                    {isPositive ? '+' : ''}{stock.price_change_percent.toFixed(2)}%
                  </span>
                  {isBestPerformer && (
                    <span className="text-xs text-primary-400 font-bold">★ Best</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Zoom Controls */}
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={handleZoomIn}
            className="p-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            disabled={zoomStart === null || zoomEnd === null}
            className="p-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetZoom}
            disabled={zoomStart === null || zoomEnd === null}
            className="p-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Reset Zoom"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0 relative">
        {displayedData.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>No data available</p>
          </div>
        ) : (
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart 
            data={displayedData} 
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <defs>
              {stocksData.map((stock, index) => {
                const color = STOCK_COLORS[index % STOCK_COLORS.length];
                return (
                  <linearGradient key={`gradient-${stock.symbol}`} id={`gradient-${stock.symbol}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
                );
              })}
            </defs>
            
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            
            <XAxis
              dataKey="time"
              stroke="#6b7280"
              fontSize={11}
              tick={{ fill: '#9ca3af' }}
              axisLine={{ stroke: '#374151' }}
              interval="preserveStartEnd"
            />
            
            <YAxis
              stroke="#6b7280"
              fontSize={11}
              tick={{ fill: '#9ca3af' }}
              axisLine={{ stroke: '#374151' }}
              domain={[Math.floor(priceRange.min), Math.ceil(priceRange.max)]}
              width={60}
              allowDataOverflow={false}
            />
            
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
            />
            
            {/* Render lines for each stock */}
            {stocksData.map((stock, index) => {
              const color = STOCK_COLORS[index % STOCK_COLORS.length];
              const symbol = stock.symbol;
              
              // Debug: Check if data exists for this stock
              const dataPoints = displayedData.filter(p => {
                const actual = p[`${symbol}_actual`];
                const predicted = p[`${symbol}_predicted`];
                return (actual !== null && actual !== undefined && !isNaN(actual)) ||
                       (predicted !== null && predicted !== undefined && !isNaN(predicted));
              });
              
              if (dataPoints.length === 0) {
                console.warn(`No valid data points for ${symbol} in displayedData`);
                return null;
              }
              
              const actualCount = dataPoints.filter(p => {
                const val = p[`${symbol}_actual`];
                return val !== null && val !== undefined && !isNaN(val);
              }).length;
              const predictedCount = dataPoints.filter(p => {
                const val = p[`${symbol}_predicted`];
                return val !== null && val !== undefined && !isNaN(val);
              }).length;
              
              console.log(`Rendering ${symbol}: ${dataPoints.length} total points, ${actualCount} actual, ${predictedCount} predicted`);
              
              return (
                <React.Fragment key={symbol}>
                  {/* Actual price line */}
                  {filters.showActualPrice && actualCount > 0 && (
                    <Area
                      type="monotone"
                      dataKey={`${symbol}_actual`}
                      stroke={color}
                      strokeWidth={2.5}
                      fill={`url(#gradient-${symbol})`}
                      name={`${symbol} Actual`}
                      connectNulls={true}
                      dot={false}
                      isAnimationActive={false}
                    />
                  )}
                  
                  {/* Predicted price line */}
                  {filters.showPredictedPrice && predictedCount > 0 && (
                    <Line
                      type="monotone"
                      dataKey={`${symbol}_predicted`}
                      stroke={color}
                      strokeWidth={2.5}
                      strokeDasharray="5 5"
                      name={`${symbol} Predicted`}
                      connectNulls={true}
                      dot={false}
                      isAnimationActive={false}
                    />
                  )}
                </React.Fragment>
              );
            })}
            
            {/* Brush for timeline navigation */}
            <Brush
              dataKey="time"
              height={30}
              stroke="#4b5563"
              fill="#1f2937"
              startIndex={zoomStart || 0}
              endIndex={zoomEnd !== null ? zoomEnd : chartData.length - 1}
              onChange={(brushData: any) => {
                if (brushData && brushData.startIndex !== undefined && brushData.endIndex !== undefined) {
                  setZoomStart(brushData.startIndex);
                  setZoomEnd(brushData.endIndex);
                }
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

