"""
Cost Optimization Package

This package contains cost optimization strategies for GPT-4 API usage.

Components:
- CostOptimizer: Batching, request optimization, cost monitoring

Why this package exists:
- Reduces API costs through intelligent batching
- Optimizes request payloads
- Monitors and tracks API usage
- Separates optimization logic from main agent
"""

from .cost_optimizer import CostOptimizer

__all__ = [
    "CostOptimizer",
]

