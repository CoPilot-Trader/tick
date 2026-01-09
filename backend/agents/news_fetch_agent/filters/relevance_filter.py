"""
Relevance Filter

This module provides relevance scoring and filtering for news articles.
It calculates how relevant each article is to a specific stock ticker.

Relevance Score:
- Range: 0.0 to 1.0
- 0.0 = Not relevant at all
- 1.0 = Highly relevant (directly about the stock)

Scoring Factors:
- Keyword matching (ticker name, company name)
- Title/headline relevance
- Content analysis
- Source reliability
"""

from typing import List, Dict, Any, Optional
import re


class RelevanceFilter:
    """
    Filters and scores news articles by relevance to a stock ticker.
    
    This class calculates relevance scores for articles and filters them
    based on a minimum threshold. Articles below the threshold are removed.
    
    Example:
        filter = RelevanceFilter()
        scored_articles = filter.score_articles(articles, "AAPL")
        filtered = filter.filter_by_threshold(scored_articles, min_score=0.5)
    """
    
    # Company name mapping for common tickers
    COMPANY_NAMES: Dict[str, List[str]] = {
        "AAPL": ["Apple", "Apple Inc", "Apple Inc.", "iPhone", "iPad", "MacBook", "iMac", "iOS", "macOS"],
        "MSFT": ["Microsoft", "Microsoft Corp", "Windows", "Azure", "Office", "Xbox", "Surface"],
        "GOOGL": ["Google", "Alphabet", "Alphabet Inc", "YouTube", "Android", "Chrome", "Gmail", "Google Cloud"],
        "GOOG": ["Google", "Alphabet", "Alphabet Inc", "YouTube", "Android", "Chrome", "Gmail", "Google Cloud"],
        "AMZN": ["Amazon", "Amazon.com", "AWS", "Alexa", "Prime"],
        "META": ["Meta", "Facebook", "Instagram", "WhatsApp", "Oculus", "VR"],
        "NVDA": ["NVIDIA", "Nvidia", "GeForce", "RTX", "CUDA"],
        "TSLA": ["Tesla", "Tesla Inc", "Model S", "Model 3", "Model X", "Model Y", "Cybertruck"],
        "NFLX": ["Netflix", "Netflix Inc", "streaming"],
        "INTC": ["Intel", "Intel Corp", "Core i7", "Core i9", "Xeon"],
        "XOM": ["Exxon Mobil", "Exxon", "ExxonMobil", "Mobil"],
        "CVX": ["Chevron", "Chevron Corp", "Chevron Corporation"],
        "SLB": ["Schlumberger", "Schlumberger Limited"],
        "COP": ["ConocoPhillips", "Conoco Phillips"],
        "EOG": ["EOG Resources", "EOG"],
        "JNJ": ["Johnson & Johnson", "J&J", "Johnson and Johnson"],
        "PFE": ["Pfizer", "Pfizer Inc", "Comirnaty"],
        "UNH": ["UnitedHealth", "UnitedHealth Group", "United Healthcare"],
        "ABBV": ["AbbVie", "Abbvie"],
        "TMO": ["Thermo Fisher", "Thermo Fisher Scientific"],
        "JPM": ["JPMorgan", "JPMorgan Chase", "JP Morgan", "Chase Bank"],
        "BAC": ["Bank of America", "BofA", "Merrill Lynch"],
        "GS": ["Goldman Sachs", "Goldman"],
        "MS": ["Morgan Stanley"],
        "WFC": ["Wells Fargo", "Wells Fargo Bank"],
        "WMT": ["Walmart", "Walmart Inc"],
        "PG": ["Procter & Gamble", "P&G", "Procter and Gamble"],
        "KO": ["Coca-Cola", "Coke"],
        "PEP": ["PepsiCo", "Pepsi"],
        "MCD": ["McDonald's", "McDonalds"],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the relevance filter.
        
        Args:
            config: Optional configuration:
                   - min_relevance_score: Minimum score to keep (default: 0.5)
                   - keyword_weight: Weight for keyword matching (default: 0.4)
                   - title_weight: Weight for title relevance (default: 0.3)
                   - content_weight: Weight for content analysis (default: 0.3)
        """
        self.config = config or {}
        self.min_relevance_score = self.config.get("min_relevance_score", 0.5)
        self.keyword_weight = self.config.get("keyword_weight", 0.4)
        self.title_weight = self.config.get("title_weight", 0.3)
        self.content_weight = self.config.get("content_weight", 0.3)
    
    def _get_keywords(self, symbol: str) -> List[str]:
        """
        Get all keywords to search for a given symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            List of keywords (symbol + company names)
        """
        keywords = [symbol.upper()]
        company_names = self.COMPANY_NAMES.get(symbol.upper(), [])
        keywords.extend(company_names)
        return keywords
    
    def _count_matches(self, text: str, keywords: List[str]) -> float:
        """
        Count keyword matches in text, normalized by text length.
        
        Improved algorithm that gives higher scores for company name matches.
        
        Args:
            text: Text to search
            keywords: List of keywords to find
        
        Returns:
            Match score between 0.0 and 1.0
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Prioritize primary keywords (symbol and main company name)
        primary_keywords = keywords[:2] if len(keywords) >= 2 else keywords
        secondary_keywords = keywords[2:] if len(keywords) > 2 else []
        
        # Check for primary keywords (higher weight)
        primary_score = 0.0
        primary_matches = 0
        for keyword in primary_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                primary_matches += 1
                # Primary keywords get significant weight
                # If found, give at least 0.6 per keyword (increased from previous)
                primary_score += 0.6
        
        # Normalize primary score
        if primary_keywords:
            primary_score = min(primary_score / len(primary_keywords), 1.0)
            # Boost if both primary keywords found
            if primary_matches >= 2:
                primary_score = min(primary_score * 1.4, 1.0)
        
        # Check for secondary keywords (lower weight but still significant)
        secondary_score = 0.0
        if secondary_keywords:
            unique_secondary_matches = sum(1 for keyword in secondary_keywords if keyword.lower() in text_lower)
            # Secondary keywords contribute more (increased from 0.3 to 0.5)
            secondary_score = min(unique_secondary_matches / max(len(secondary_keywords), 1) * 0.5, 0.5)
        
        # Combine scores (primary is more important)
        total_score = primary_score * 0.7 + secondary_score * 0.3
        
        # Boost if multiple unique keywords found (more generous)
        unique_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        if unique_matches >= 2:
            total_score = min(total_score * 1.5, 1.0)  # Boost by 50% if multiple keywords (increased from 30%)
        elif unique_matches >= 1:
            total_score = min(total_score * 1.2, 1.0)  # Small boost even for single match
        
        # Minimum score if any keyword is found
        if unique_matches > 0:
            total_score = max(total_score, 0.3)  # Ensure at least 0.3 if any keyword found
        
        return min(total_score, 1.0)
    
    def calculate_relevance(self, article: Dict[str, Any], symbol: str) -> float:
        """
        Calculate relevance score for a single article.
        
        This method analyzes the article and calculates how relevant it is
        to the given stock symbol. The score is between 0.0 and 1.0.
        
        Args:
            article: News article dictionary with:
                   - title: Article title
                   - content: Article content/text
                   - summary: Article summary (optional)
            symbol: Stock symbol (e.g., "AAPL")
        
        Returns:
            Relevance score between 0.0 and 1.0
        
        Algorithm:
            1. Extract keywords (symbol, company name, ticker variations)
            2. Check title for keyword matches (weight: 0.4)
            3. Check content for keyword matches (weight: 0.4)
            4. Check summary for keyword matches (weight: 0.2)
            5. Combine scores with weights
            6. Return final score
        
        Example:
            score = filter.calculate_relevance(article, "AAPL")
            # Returns: 0.95 (highly relevant)
        """
        # Get keywords for this symbol
        keywords = self._get_keywords(symbol)
        
        if not keywords:
            return 0.0
        
        # Extract text fields
        title = article.get("title", "") or ""
        content = article.get("content", "") or ""
        summary = article.get("summary", "") or ""
        
        # Calculate match scores for each field
        title_score = self._count_matches(title, keywords)
        content_score = self._count_matches(content, keywords)
        summary_score = self._count_matches(summary, keywords)
        
        # If we have summary, use it; otherwise rely on content
        if summary:
            # Title is most important (50%), then content (30%), then summary (20%)
            final_score = (
                title_score * 0.5 +
                content_score * 0.3 +
                summary_score * 0.2
            )
        else:
            # Title (60%) and content (40%) - title is more important
            final_score = (
                title_score * 0.6 +
                content_score * 0.4
            )
        
        # Boost score if symbol or company name appears in title (direct mention is very relevant)
        if symbol.upper() in title.upper():
            final_score = min(final_score * 1.8, 1.0)  # Strong boost for symbol in title (increased from 1.5)
        elif any(keyword.lower() in title.lower() for keyword in keywords[:3]):  # Top 3 keywords
            final_score = min(final_score * 1.5, 1.0)  # Moderate boost for company name in title (increased from 1.2)
        
        # Additional boost if company name appears in content (even if not in title)
        if any(keyword.lower() in content.lower() for keyword in keywords[:2]):  # Primary keywords
            final_score = min(final_score * 1.2, 1.0)  # Boost for company name in content
        
        # Ensure minimum score if any keyword found anywhere
        if any(keyword.lower() in (title + content + summary).lower() for keyword in keywords):
            final_score = max(final_score, 0.35)  # Minimum 0.35 if any keyword found (helps pass 0.4 threshold)
        
        # Ensure score is between 0.0 and 1.0
        return min(max(final_score, 0.0), 1.0)
    
    def score_articles(self, articles: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
        """
        Calculate relevance scores for multiple articles.
        
        Args:
            articles: List of news articles
            symbol: Stock symbol
        
        Returns:
            List of articles with added "relevance_score" field
        
        Example:
            articles = [
                {"title": "Apple Reports Earnings", "content": "..."},
                {"title": "Tech Stocks Rally", "content": "..."}
            ]
            scored = filter.score_articles(articles, "AAPL")
            # Returns articles with relevance_score added
        """
        # TODO: Implement batch scoring
        # For each article:
        #   1. Calculate relevance score
        #   2. Add "relevance_score" field to article
        #   3. Return updated articles
        
        scored_articles = []
        for article in articles:
            score = self.calculate_relevance(article, symbol)
            article["relevance_score"] = score
            scored_articles.append(article)
        
        return scored_articles
    
    def filter_by_threshold(self, articles: List[Dict[str, Any]], min_score: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Filter articles by relevance score threshold.
        
        Args:
            articles: List of articles with relevance_score field
            min_score: Minimum relevance score (default: from config)
        
        Returns:
            Filtered list of articles (only those above threshold)
        
        Example:
            filtered = filter.filter_by_threshold(scored_articles, min_score=0.5)
            # Returns only articles with relevance_score >= 0.5
        """
        if min_score is None:
            min_score = self.min_relevance_score
        
        return [
            article for article in articles
            if article.get("relevance_score", 0.0) >= min_score
        ]
    
    def sort_by_relevance(self, articles: List[Dict[str, Any]], reverse: bool = True) -> List[Dict[str, Any]]:
        """
        Sort articles by relevance score.
        
        Args:
            articles: List of articles with relevance_score field
            reverse: If True, sort descending (highest first)
        
        Returns:
            Sorted list of articles
        
        Example:
            sorted_articles = filter.sort_by_relevance(articles)
            # Returns articles sorted by relevance (highest first)
        """
        return sorted(
            articles,
            key=lambda x: x.get("relevance_score", 0.0),
            reverse=reverse
        )

