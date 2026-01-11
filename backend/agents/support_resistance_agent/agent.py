import json
import os
import pandas as pd
from ..base_agent import BaseAgent
from .levels_algo import SupportResistanceAlgo

class SupportResistanceAgent(BaseAgent):
    def __init__(self, window=10):
        super().__init__()
        self.algo = SupportResistanceAlgo(window=window)
        self.cached_levels = []
        
    def train(self, data_path: str, **kwargs):
        """
        algorithm isn't 'trained' via gradient descent, but we can 
        pre-calculate levels from historical data here.
        """
        print(f"SRAgent: Finding levels in {data_path}...")
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            # Ensure proper casting
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            
            self.cached_levels = self.algo.find_levels(df)
            print(f"SRAgent: Found {len(self.cached_levels)} levels.")
        except Exception as e:
            print(f"SRAgent Error: {e}")

    def predict(self, input_data):
        """
        For S/R, 'predict' might mean returning the list of active levels 
        relevant to the current price, or just all levels.
        """
        # input_data is ignored in this simple version, typically we'd filter for tiers close to current price
        return self.cached_levels

    def save(self, path: str):
        # We save the computed levels
        with open(path, 'w') as f:
            json.dump(self.cached_levels, f)
        print(f"SRAgent: Levels saved to {path}")

    def load(self, path: str):
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.cached_levels = json.load(f)
            print(f"SRAgent: Levels loaded from {path}")
        else:
            print(f"SRAgent: No state found at {path}")
