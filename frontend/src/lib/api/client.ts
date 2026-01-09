// API client for backend connection
// Currently uses mock data, but ready to connect to backend

import { StockData } from '@/types';
import { generateMockStockData, getAllMockStocks } from '@/lib/mockData';

// API base URL - can be configured via environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * API Client for fetching stock data
 * Currently uses mock data, but can be extended to call real backend API
 */
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get all available stocks
   * @returns Promise resolving to array of StockData
   */
  async getStocks(): Promise<StockData[]> {
    // TODO: Replace with actual API call
    // return this.fetchFromAPI('/api/v1/stocks');
    return getAllMockStocks();
  }

  /**
   * Get stock data for a given symbol
   * @param symbol Stock symbol (e.g., 'AAPL', 'MSFT')
   * @returns Promise resolving to StockData
   */
  async getStockData(symbol: string): Promise<StockData> {
    // For now, use mock data
    // TODO: Replace with actual API call when backend is ready
    // return this.fetchFromAPI(`/api/v1/stocks/${symbol}`);
    return generateMockStockData(symbol);
  }

  /**
   * Get real-time updates for a stock
   * @param symbol Stock symbol
   * @returns Promise resolving to StockData
   */
  async getRealtimeData(symbol: string): Promise<StockData> {
    // TODO: Replace with WebSocket or polling
    // return this.fetchFromAPI(`/api/v1/stocks/${symbol}/realtime`);
    return generateMockStockData(symbol);
  }

  /**
   * Get multiple stocks data
   * @param symbols Array of stock symbols
   * @returns Promise resolving to array of StockData
   */
  async getMultipleStocksData(symbols: string[]): Promise<StockData[]> {
    return Promise.all(symbols.map(symbol => this.getStockData(symbol)));
  }

  /**
   * Fetch data from the backend API
   * @param endpoint API endpoint path
   * @returns Promise resolving to data
   */
  private async fetchFromAPI<T>(endpoint: string): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error fetching from ${endpoint}:`, error);
      throw error;
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
