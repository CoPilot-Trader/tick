"""
Sector Mapper

This module provides mapping from stock tickers to their sectors/industries.
This metadata is used for sector-aware filtering and analysis.

Why Sector Mapping?
- Different sectors have different news patterns
- Tech sector news != Energy sector news
- Helps with relevance filtering
- Useful for sector-specific analysis

Sector Categories:
- Technology: AAPL, MSFT, GOOGL, etc.
- Energy: XOM, CVX, SLB, etc.
- Healthcare: JNJ, PFE, UNH, etc.
- Finance: JPM, BAC, GS, etc.
- Consumer: WMT, PG, KO, etc.
"""

from typing import Dict, Optional


class SectorMapper:
    """
    Maps stock tickers to their sectors/industries.
    
    This class provides sector information for tickers, which is used
    for sector-aware news filtering and analysis.
    
    Example:
        mapper = SectorMapper()
        sector = mapper.get_sector("AAPL")  # Returns: "technology"
        sector = mapper.get_sector("XOM")     # Returns: "energy"
    """
    
    # Sector mapping dictionary
    # This can be loaded from a database or config file in production
    SECTOR_MAP: Dict[str, str] = {
        # Technology
        "AAPL": "technology",
        "MSFT": "technology",
        "GOOGL": "technology",
        "GOOG": "technology",
        "AMZN": "technology",
        "META": "technology",
        "NVDA": "technology",
        "TSLA": "technology",
        "NFLX": "technology",
        "INTC": "technology",
        
        # Energy
        "XOM": "energy",
        "CVX": "energy",
        "SLB": "energy",
        "COP": "energy",
        "EOG": "energy",
        
        # Healthcare
        "JNJ": "healthcare",
        "PFE": "healthcare",
        "UNH": "healthcare",
        "ABBV": "healthcare",
        "TMO": "healthcare",
        
        # Finance
        "JPM": "finance",
        "BAC": "finance",
        "GS": "finance",
        "MS": "finance",
        "WFC": "finance",
        
        # Consumer
        "WMT": "consumer",
        "PG": "consumer",
        "KO": "consumer",
        "PEP": "consumer",
        "MCD": "consumer",
        
        # Add more tickers as needed
    }
    
    def __init__(self, custom_map: Optional[Dict[str, str]] = None):
        """
        Initialize sector mapper.
        
        Args:
            custom_map: Optional custom sector mapping to override defaults
        """
        self.sector_map = self.SECTOR_MAP.copy()
        if custom_map:
            self.sector_map.update(custom_map)
    
    def get_sector(self, symbol: str) -> Optional[str]:
        """
        Get sector for a given stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")
        
        Returns:
            Sector name (e.g., "technology", "energy") or None if not found
        
        Example:
            sector = mapper.get_sector("AAPL")
            # Returns: "technology"
        """
        return self.sector_map.get(symbol.upper())
    
    def get_tickers_by_sector(self, sector: str) -> list[str]:
        """
        Get all tickers in a given sector.
        
        Args:
            sector: Sector name (e.g., "technology", "energy")
        
        Returns:
            List of ticker symbols in that sector
        
        Example:
            tech_tickers = mapper.get_tickers_by_sector("technology")
            # Returns: ["AAPL", "MSFT", "GOOGL", ...]
        """
        return [
            ticker for ticker, ticker_sector in self.sector_map.items()
            if ticker_sector.lower() == sector.lower()
        ]
    
    def add_ticker(self, symbol: str, sector: str) -> None:
        """
        Add or update a ticker-sector mapping.
        
        Args:
            symbol: Stock symbol
            sector: Sector name
        
        Example:
            mapper.add_ticker("NEWT", "technology")
        """
        self.sector_map[symbol.upper()] = sector.lower()
    
    def has_sector(self, symbol: str) -> bool:
        """
        Check if a ticker has sector information.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            True if sector is known, False otherwise
        
        Example:
            has_sector = mapper.has_sector("AAPL")  # Returns: True
            has_sector = mapper.has_sector("UNKNOWN")  # Returns: False
        """
        return symbol.upper() in self.sector_map
    
    def get_all_sectors(self) -> list[str]:
        """
        Get list of all sectors in the mapping.
        
        Returns:
            List of unique sector names
        
        Example:
            sectors = mapper.get_all_sectors()
            # Returns: ["technology", "energy", "healthcare", ...]
        """
        return sorted(list(set(self.sector_map.values())))

