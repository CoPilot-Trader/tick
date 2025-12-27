'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Dot,
} from 'recharts';
import { StockData, PredictionPoint } from '@/types';
import { format } from 'date-fns';

interface PriceChartProps {
  data: StockData;
  selectedPrediction: PredictionPoint | null;
  onPredictionClick: (prediction: PredictionPoint | null) => void;
}

interface ChartDataPoint {
  timestamp: string;
  time: string;
  actual: number | null;
  predicted: number | null;
  upper_bound: number | null;
  lower_bound: number | null;
  isPrediction: boolean;
  prediction?: PredictionPoint;
}

export default function PriceChart({ data, selectedPrediction, onPredictionClick }: PriceChartProps) {
  const chartData = useMemo(() => {
    const points: ChartDataPoint[] = [];

    // Add historical data (actual prices)
    data.historical_data.slice(-100).forEach((point) => {
      points.push({
        timestamp: point.timestamp,
        time: format(new Date(point.timestamp), 'MMM dd HH:mm'),
        actual: point.close,
        predicted: null,
        upper_bound: null,
        lower_bound: null,
        isPrediction: false,
      });
    });

    // Add predictions (every 5 minutes, showing every 12th point for readability)
    data.predictions.filter((_, index) => index % 12 === 0).forEach((prediction) => {
      points.push({
        timestamp: prediction.timestamp,
        time: format(new Date(prediction.timestamp), 'MMM dd HH:mm'),
        actual: null,
        predicted: prediction.predicted_price,
        upper_bound: prediction.upper_bound,
        lower_bound: prediction.lower_bound,
        isPrediction: true,
        prediction,
      });
    });

    return points;
  }, [data]);

  // Support and resistance levels
  const supportLevels = data.support_levels.map(level => level.price);
  const resistanceLevels = data.resistance_levels.map(level => level.price);

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload.isPrediction) return null;

    const isSelected = selectedPrediction?.timestamp === payload.timestamp;
    
    return (
      <Dot
        cx={cx}
        cy={cy}
        r={isSelected ? 6 : 4}
        fill={isSelected ? '#0ea5e9' : '#8b5cf6'}
        stroke={isSelected ? '#0284c7' : '#6d28d9'}
        strokeWidth={isSelected ? 2 : 1}
        onClick={() => onPredictionClick(payload.prediction)}
        style={{ cursor: 'pointer' }}
      />
    );
  };

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-sm p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{data.symbol} Price Chart</h3>
        <p className="text-sm text-gray-500">Real prices and 5-minute predictions</p>
      </div>
      
      <ResponsiveContainer width="100%" height={500}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="time"
            stroke="#6b7280"
            fontSize={12}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            domain={['dataMin - 5', 'dataMax + 5']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number, name: string) => [
              `$${value.toFixed(2)}`,
              name === 'actual' ? 'Actual Price' : name === 'predicted' ? 'Predicted Price' : name,
            ]}
          />
          <Legend />
          
          {/* Support levels */}
          {supportLevels.map((level, index) => (
            <ReferenceLine
              key={`support-${index}`}
              y={level}
              stroke="#22c55e"
              strokeDasharray="5 5"
              label={{ value: `Support $${level.toFixed(2)}`, position: 'right' }}
            />
          ))}
          
          {/* Resistance levels */}
          {resistanceLevels.map((level, index) => (
            <ReferenceLine
              key={`resistance-${index}`}
              y={level}
              stroke="#ef4444"
              strokeDasharray="5 5"
              label={{ value: `Resistance $${level.toFixed(2)}`, position: 'right' }}
            />
          ))}
          
          {/* Actual price line */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Actual Price"
            connectNulls={false}
          />
          
          {/* Predicted price line */}
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#8b5cf6"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={<CustomDot />}
            name="Predicted Price"
            connectNulls={false}
          />
          
          {/* Confidence bounds */}
          <Line
            type="monotone"
            dataKey="upper_bound"
            stroke="#8b5cf6"
            strokeWidth={1}
            strokeDasharray="2 2"
            dot={false}
            name="Upper Bound"
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="lower_bound"
            stroke="#8b5cf6"
            strokeWidth={1}
            strokeDasharray="2 2"
            dot={false}
            name="Lower Bound"
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="mt-4 flex items-center gap-4 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-blue-500"></div>
          <span>Actual Price</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-purple-500 border-dashed border"></div>
          <span>Predicted Price</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-green-500 border-dashed border"></div>
          <span>Support Level</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-red-500 border-dashed border"></div>
          <span>Resistance Level</span>
        </div>
      </div>
    </div>
  );
}


