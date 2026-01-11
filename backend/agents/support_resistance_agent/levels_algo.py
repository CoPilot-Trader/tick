import pandas as pd
import numpy as np
from typing import List, Tuple

class SupportResistanceAlgo:
    def __init__(self, window=10):
        self.window = window

    def find_levels(self, df: pd.DataFrame) -> List[float]:
        """
        Identifies local minima and maxima as support/resistance levels.
        """
        levels = []
        if 'high' not in df.columns or 'low' not in df.columns:
            return [] # or raise Error

        # Heuristic: Find local Maxima (Resistance) and Minima (Support)
        # We scroll through the data and check if a point is higher/lower than neighbors
        
        highs = df['high'].values
        lows = df['low'].values
        
        # Simple local extrema
        for i in range(self.window, len(df) - self.window):
            if np.all(highs[i] > highs[i-self.window : i]) and \
               np.all(highs[i] > highs[i+1 : i+1+self.window]):
                levels.append(float(highs[i]))
                
            if np.all(lows[i] < lows[i-self.window : i]) and \
               np.all(lows[i] < lows[i+1 : i+1+self.window]):
                levels.append(float(lows[i]))
                
        # Deduplicate close levels might be a good next step, but keeping it simple for now
        return sorted(list(set(levels))) # Unique sorted levels
