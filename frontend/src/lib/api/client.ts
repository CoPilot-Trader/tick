// API client for backend connection
// Currently uses mock data, but ready to connect to backend

import { StockData } from '@/types';
import { generateMockStockData, getAllMockStocks } from '@/lib/mockData';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Get all available stocks
  async getStocks(): Promise<StockData[]> {
    // TODO: Replace with actual API call
    // return fetch(`${this.baseUrl}/api/v1/stocks`).then(res => res.json());
    return getAllMockStocks();
  }

  // Get stock data with predictions
  async getStockData(symbol: string): Promise<StockData> {
    // TODO: Replace with actual API call
    // return fetch(`${this.baseUrl}/api/v1/stocks/${symbol}`).then(res => res.json());
    return generateMockStockData(symbol);
  }

  // Get real-time updates
  async getRealtimeData(symbol: string): Promise<StockData> {
    // TODO: Replace with WebSocket or polling
    // return fetch(`${this.baseUrl}/api/v1/stocks/${symbol}/realtime`).then(res => res.json());
    return generateMockStockData(symbol);
  }
}

export const apiClient = new ApiClient();

