"""
Prompt Templates for Sentiment Analysis

This module contains prompt templates for GPT-4 sentiment analysis.
These prompts are optimized to extract sentiment scores and labels from news articles.

Why Prompt Templates?
- Consistent prompt structure
- Easy to modify and optimize
- Centralized prompt management
- Version control for prompts
"""

from typing import Dict, Any


class PromptTemplates:
    """
    Prompt templates for sentiment analysis.
    
    These templates are designed to extract:
    - Sentiment score (-1.0 to +1.0)
    - Sentiment label (positive, neutral, negative)
    - Confidence score (0.0 to 1.0)
    """
    
    SENTIMENT_ANALYSIS_PROMPT = """You are a financial sentiment analysis expert. Analyze the following news article about {symbol} ({company_name}) and provide a sentiment assessment.

Article Title: {title}
Article Content: {content}

Please analyze the sentiment of this article and provide your response in the following JSON format:
{{
    "sentiment_score": <float between -1.0 and +1.0, where -1.0 is very negative and +1.0 is very positive>,
    "sentiment_label": "<positive|neutral|negative>",
    "confidence": <float between 0.0 and 1.0, indicating confidence in the analysis>,
    "reasoning": "<brief explanation of your sentiment assessment>"
}}

Guidelines:
- Consider the overall tone and implications for the stock
- Positive news (earnings beat, product launches, partnerships) should score > 0.5
- Negative news (lawsuits, declining sales, regulatory issues) should score < -0.5
- Neutral news (general updates, routine announcements) should score between -0.3 and +0.3
- Be conservative with extreme scores (only use > 0.8 or < -0.8 for very strong sentiment)
- Confidence should reflect how clear the sentiment is (high for obvious cases, lower for ambiguous)

Respond with ONLY the JSON object, no additional text."""

    SENTIMENT_ANALYSIS_PROMPT_SIMPLE = """Analyze the sentiment of this financial news article about {symbol}:

Title: {title}
Content: {content}

Provide sentiment as JSON:
{{
    "sentiment_score": <float -1.0 to +1.0>,
    "sentiment_label": "<positive|neutral|negative>",
    "confidence": <float 0.0 to 1.0>,
    "reasoning": "<brief explanation>"
}}"""

    @staticmethod
    def get_sentiment_prompt(article: Dict[str, Any], symbol: str, company_name: str = None) -> str:
        """
        Generate sentiment analysis prompt for an article.
        
        Args:
            article: News article dictionary with title and content
            symbol: Stock symbol (e.g., "AAPL")
            company_name: Company name (e.g., "Apple Inc") - optional
        
        Returns:
            Formatted prompt string
        
        Example:
            prompt = PromptTemplates.get_sentiment_prompt(article, "AAPL", "Apple Inc")
        """
        if company_name is None:
            company_name = symbol
        
        title = article.get("title", "")
        content = article.get("content", "") or article.get("summary", "")
        
        # Truncate content if too long (GPT-4 has token limits)
        max_content_length = 2000  # Approximate character limit
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        return PromptTemplates.SENTIMENT_ANALYSIS_PROMPT.format(
            symbol=symbol,
            company_name=company_name,
            title=title,
            content=content
        )
    
    @staticmethod
    def get_batch_prompt(articles: list[Dict[str, Any]], symbol: str) -> str:
        """
        Generate batch sentiment analysis prompt for multiple articles.
        
        Args:
            articles: List of news articles
            symbol: Stock symbol
        
        Returns:
            Formatted prompt string for batch analysis
        
        Note:
            Batch prompts are more efficient but may have lower quality.
            Use for cost optimization when processing many articles.
        """
        articles_text = ""
        for i, article in enumerate(articles[:10], 1):  # Limit to 10 articles per batch
            title = article.get("title", "")
            content = article.get("content", "") or article.get("summary", "")
            if len(content) > 500:
                content = content[:500] + "..."
            
            articles_text += f"\n\nArticle {i}:\nTitle: {title}\nContent: {content}\n"
        
        return f"""Analyze the sentiment of the following {len(articles)} news articles about {symbol}.

{articles_text}

For each article, provide sentiment as JSON array:
[
    {{
        "article_index": 1,
        "sentiment_score": <float -1.0 to +1.0>,
        "sentiment_label": "<positive|neutral|negative>",
        "confidence": <float 0.0 to 1.0>
    }},
    ...
]

Respond with ONLY the JSON array, no additional text."""

