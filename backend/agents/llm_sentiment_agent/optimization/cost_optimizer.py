"""
Cost Optimizer for GPT-4 API

This module provides cost optimization strategies for GPT-4 API usage.

Optimization Strategies:
- Batching requests
- Request payload optimization
- Cost monitoring and tracking
- Intelligent caching

Why Cost Optimization?
- GPT-4 API is expensive
- Reduce unnecessary API calls
- Optimize request payloads
- Monitor and control costs
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class CostOptimizer:
    """
    Cost optimizer for GPT-4 API usage.
    
    Provides strategies to reduce API costs through batching,
    payload optimization, and cost tracking.
    
    Example:
        optimizer = CostOptimizer()
        batches = optimizer.create_batches(articles, batch_size=5)
        cost = optimizer.estimate_cost(articles)
    """
    
    # GPT-4 pricing (as of 2024, adjust as needed)
    # Input: $0.03 per 1K tokens
    # Output: $0.06 per 1K tokens
    INPUT_COST_PER_1K = 0.03
    OUTPUT_COST_PER_1K = 0.06
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cost optimizer.
        
        Args:
            config: Optional configuration:
                   - batch_size: Default batch size (default: 5)
                   - max_batch_size: Maximum batch size (default: 10)
                   - track_costs: Track cost statistics (default: True)
        """
        self.config = config or {}
        self.batch_size = self.config.get("batch_size", 5)
        self.max_batch_size = self.config.get("max_batch_size", 10)
        self.track_costs = self.config.get("track_costs", True)
        
        # Cost tracking
        self._cost_stats = {
            "total_requests": 0,
            "total_tokens_input": 0,
            "total_tokens_output": 0,
            "total_cost": 0.0,
            "requests_by_date": {}
        }
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.
        
        Rough estimation: ~4 characters per token for English text.
        More accurate would require tiktoken library.
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        
        Example:
            tokens = optimizer.estimate_tokens("Hello world")
            # Returns: ~3 tokens
        """
        # Rough estimation: 4 characters per token
        return len(text) // 4
    
    def estimate_cost(self, articles: List[Dict[str, Any]], prompt_template: str = "") -> Dict[str, Any]:
        """
        Estimate cost for analyzing articles.
        
        Args:
            articles: List of news articles
            prompt_template: Prompt template (for estimating input tokens)
        
        Returns:
            Dictionary with cost estimates:
            {
                "estimated_input_tokens": int,
                "estimated_output_tokens": int,
                "estimated_cost": float,
                "cost_per_article": float
            }
        
        Example:
            cost_estimate = optimizer.estimate_cost(articles)
            print(f"Estimated cost: ${cost_estimate['estimated_cost']:.4f}")
        """
        total_input_tokens = 0
        estimated_output_tokens = 200  # Average output tokens per article
        
        for article in articles:
            # Estimate input tokens
            title = article.get("title", "")
            content = article.get("content", "") or article.get("summary", "")
            article_text = f"{title} {content}"
            
            # Truncate if too long
            if len(article_text) > 2000:
                article_text = article_text[:2000]
            
            prompt_text = prompt_template.format(
                symbol=article.get("symbol", ""),
                title=title,
                content=article_text
            )
            
            input_tokens = self.estimate_tokens(prompt_text)
            total_input_tokens += input_tokens
        
        # Calculate costs
        input_cost = (total_input_tokens / 1000) * self.INPUT_COST_PER_1K
        output_cost = (len(articles) * estimated_output_tokens / 1000) * self.OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost
        
        return {
            "estimated_input_tokens": total_input_tokens,
            "estimated_output_tokens": len(articles) * estimated_output_tokens,
            "estimated_cost": total_cost,
            "cost_per_article": total_cost / len(articles) if articles else 0.0,
            "num_articles": len(articles)
        }
    
    def create_batches(self, articles: List[Dict[str, Any]], batch_size: Optional[int] = None) -> List[List[Dict[str, Any]]]:
        """
        Create batches of articles for batch processing.
        
        Args:
            articles: List of news articles
            batch_size: Batch size (default: from config)
        
        Returns:
            List of article batches
        
        Example:
            batches = optimizer.create_batches(articles, batch_size=5)
            for batch in batches:
                process_batch(batch)
        """
        if batch_size is None:
            batch_size = self.batch_size
        
        # Limit batch size
        batch_size = min(batch_size, self.max_batch_size)
        
        batches = []
        for i in range(0, len(articles), batch_size):
            batches.append(articles[i:i + batch_size])
        
        return batches
    
    def track_request(self, input_tokens: int, output_tokens: int) -> None:
        """
        Track API request costs.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Example:
            optimizer.track_request(input_tokens=1000, output_tokens=200)
        """
        if not self.track_costs:
            return
        
        self._cost_stats["total_requests"] += 1
        self._cost_stats["total_tokens_input"] += input_tokens
        self._cost_stats["total_tokens_output"] += output_tokens
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * self.INPUT_COST_PER_1K
        output_cost = (output_tokens / 1000) * self.OUTPUT_COST_PER_1K
        request_cost = input_cost + output_cost
        
        self._cost_stats["total_cost"] += request_cost
        
        # Track by date
        today = datetime.utcnow().date().isoformat()
        if today not in self._cost_stats["requests_by_date"]:
            self._cost_stats["requests_by_date"][today] = {
                "requests": 0,
                "cost": 0.0
            }
        
        self._cost_stats["requests_by_date"][today]["requests"] += 1
        self._cost_stats["requests_by_date"][today]["cost"] += request_cost
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """
        Get cost statistics.
        
        Returns:
            Dictionary with cost stats:
            {
                "total_requests": int,
                "total_tokens_input": int,
                "total_tokens_output": int,
                "total_cost": float,
                "average_cost_per_request": float,
                "requests_by_date": dict
            }
        
        Example:
            stats = optimizer.get_cost_stats()
            print(f"Total cost: ${stats['total_cost']:.2f}")
        """
        stats = self._cost_stats.copy()
        
        # Calculate average cost per request
        if stats["total_requests"] > 0:
            stats["average_cost_per_request"] = stats["total_cost"] / stats["total_requests"]
        else:
            stats["average_cost_per_request"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset cost statistics."""
        self._cost_stats = {
            "total_requests": 0,
            "total_tokens_input": 0,
            "total_tokens_output": 0,
            "total_cost": 0.0,
            "requests_by_date": {}
        }
    
    def optimize_prompt(self, prompt: str, max_length: int = 2000) -> str:
        """
        Optimize prompt by truncating if necessary.
        
        Args:
            prompt: Original prompt
            max_length: Maximum character length
        
        Returns:
            Optimized prompt
        
        Example:
            optimized = optimizer.optimize_prompt(long_prompt, max_length=2000)
        """
        if len(prompt) <= max_length:
            return prompt
        
        # Truncate and add ellipsis
        return prompt[:max_length - 3] + "..."

