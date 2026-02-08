"""
Storage Module for TICK Data Agent.

Handles persistence of OHLCV data in Parquet format for the historical pipeline.
"""

from .parquet_storage import ParquetStorage

__all__ = ["ParquetStorage"]




