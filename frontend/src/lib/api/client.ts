import { StockData } from '@/types';
import { generateMockStockData } from '@/lib/mockData';

// API base URL - can be configured via environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * API Client for fetching stock data
 * Currently uses mock data, but can be extended to call real backend API
 */
class ApiClient {
  /**
   * Get stock data for a given symbol
   * @param symbol Stock symbol (e.g., 'AAPL', 'MSFT')
   * @returns Promise resolving to StockData
   */
  async getStockData(symbol: string): Promise<StockData> {
    // For now, use mock data
    // TODO: Replace with actual API call when backend is ready
    // return this.fetchFromAPI(symbol);
    return generateMockStockData(symbol);
  }

  /**
   * Fetch stock data from the backend API
   * @param symbol Stock symbol
   * @returns Promise resolving to StockData
   */
  private async fetchFromAPI(symbol: string): Promise<StockData> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/stocks/${symbol}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch stock data: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching stock data for ${symbol}:`, error);
      // Fallback to mock data on error
      return generateMockStockData(symbol);
    }
  }

  /**
   * Get multiple stocks data
   * @param symbols Array of stock symbols
   * @returns Promise resolving to array of StockData
   */
  async getMultipleStocksData(symbols: string[]): Promise<StockData[]> {
    return Promise.all(symbols.map(symbol => this.getStockData(symbol)));
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

