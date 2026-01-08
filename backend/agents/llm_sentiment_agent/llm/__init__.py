"""
LLM Module Package

This package contains GPT-4 integration and prompt templates for sentiment analysis.

Components:
- GPT4Client: OpenAI GPT-4 API client
- MockGPT4Client: Mock client for testing
- PromptTemplates: Sentiment analysis prompt templates

Why this package exists:
- Separates LLM logic from main agent
- Makes it easy to switch models or add new ones
- Allows testing with mock responses
- Centralizes prompt management
"""

from .gpt4_client import GPT4Client
from .mock_gpt4_client import MockGPT4Client
from .prompt_templates import PromptTemplates

__all__ = [
    "GPT4Client",
    "MockGPT4Client",
    "PromptTemplates",
]

