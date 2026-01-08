"""
Duplicate Filter

This module provides duplicate detection and removal for news articles.
Since we fetch from multiple sources, the same article may appear multiple times.

Duplicate Detection Methods:
- URL matching (exact match)
- Title similarity (fuzzy matching)
- Content similarity (text similarity)

Why Remove Duplicates?
- Avoid processing same article multiple times
- Reduce costs (especially for GPT-4 API)
- Cleaner data for sentiment analysis
- Better user experience
"""

from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher


class DuplicateFilter:
    """
    Detects and removes duplicate news articles.
    
    This class identifies duplicate articles from different sources
    and keeps only one copy (usually the one with highest relevance or
    from most reliable source).
    
    Example:
        filter = DuplicateFilter()
        unique_articles = filter.remove_duplicates(articles)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the duplicate filter.
        
        Args:
            config: Optional configuration:
                   - title_similarity_threshold: Title similarity for duplicate (default: 0.9)
                   - content_similarity_threshold: Content similarity for duplicate (default: 0.85)
                   - prefer_source: Preferred source when duplicates found (e.g., "Reuters")
        """
        self.config = config or {}
        self.title_threshold = self.config.get("title_similarity_threshold", 0.9)
        self.content_threshold = self.config.get("content_similarity_threshold", 0.85)
        self.prefer_source = self.config.get("prefer_source")
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Uses SequenceMatcher to calculate similarity ratio.
        
        Args:
            text1: First text string
            text2: Second text string
        
        Returns:
            Similarity score between 0.0 and 1.0
            1.0 = Identical
            0.0 = Completely different
        
        Example:
            similarity = filter._calculate_similarity("Apple Earnings", "Apple Reports Earnings")
            # Returns: 0.85 (highly similar)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _is_duplicate(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> bool:
        """
        Check if two articles are duplicates.
        
        Checks multiple criteria:
        1. URL match (exact)
        2. Title similarity (fuzzy)
        3. Content similarity (fuzzy)
        
        Args:
            article1: First article
            article2: Second article
        
        Returns:
            True if articles are duplicates, False otherwise
        """
        # Check URL match (exact)
        url1 = article1.get("url", "")
        url2 = article2.get("url", "")
        if url1 and url2 and url1 == url2:
            return True
        
        # Check title similarity
        title1 = article1.get("title", "")
        title2 = article2.get("title", "")
        if title1 and title2:
            title_sim = self._calculate_similarity(title1, title2)
            if title_sim >= self.title_threshold:
                return True
        
        # Check content similarity (if available)
        content1 = article1.get("content", "") or article1.get("summary", "")
        content2 = article2.get("content", "") or article2.get("summary", "")
        if content1 and content2:
            content_sim = self._calculate_similarity(content1, content2)
            if content_sim >= self.content_threshold:
                return True
        
        return False
    
    def remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate articles from the list.
        
        This method identifies duplicates and keeps only one copy.
        If prefer_source is set, keeps article from preferred source.
        Otherwise, keeps the first occurrence.
        
        Args:
            articles: List of news articles
        
        Returns:
            List of unique articles (duplicates removed)
        
        Algorithm:
            1. Compare each article with all others
            2. If duplicate found, keep one (prefer preferred source)
            3. Continue until all duplicates removed
        
        Example:
            articles = [
                {"title": "Apple Earnings", "source": "Reuters", "url": "url1"},
                {"title": "Apple Earnings", "source": "Bloomberg", "url": "url1"},
                {"title": "Tech Rally", "source": "Reuters", "url": "url2"}
            ]
            unique = filter.remove_duplicates(articles)
            # Returns: 2 articles (duplicate removed)
        """
        if not articles:
            return []
        
        unique_articles = []
        seen_indices = set()
        
        for i, article in enumerate(articles):
            if i in seen_indices:
                continue
            
            # Check if this article is duplicate of any already added
            is_duplicate = False
            for j, unique_article in enumerate(unique_articles):
                if self._is_duplicate(article, unique_article):
                    is_duplicate = True
                    # If current article is from preferred source, replace
                    if self.prefer_source and article.get("source") == self.prefer_source:
                        unique_articles[j] = article
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
            
            seen_indices.add(i)
        
        return unique_articles
    
    def find_duplicates(self, articles: List[Dict[str, Any]]) -> List[List[int]]:
        """
        Find groups of duplicate articles (returns indices).
        
        Useful for analysis and debugging.
        
        Args:
            articles: List of news articles
        
        Returns:
            List of duplicate groups, where each group is a list of indices
        
        Example:
            duplicates = filter.find_duplicates(articles)
            # Returns: [[0, 2], [5, 7, 9]]
            # Means articles at indices 0 and 2 are duplicates
            # And articles at indices 5, 7, 9 are duplicates
        """
        duplicate_groups = []
        processed = set()
        
        for i in range(len(articles)):
            if i in processed:
                continue
            
            group = [i]
            for j in range(i + 1, len(articles)):
                if j in processed:
                    continue
                
                if self._is_duplicate(articles[i], articles[j]):
                    group.append(j)
                    processed.add(j)
            
            if len(group) > 1:
                duplicate_groups.append(group)
                processed.add(i)
        
        return duplicate_groups

