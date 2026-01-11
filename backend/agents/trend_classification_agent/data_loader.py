import json
import pandas as pd
import numpy as np

class TrendDataLoader:
    def __init__(self, data_path: str):
        self.data_path = data_path

    def load_data(self):
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        return df

    def prepare_features_and_targets(self, df: pd.DataFrame):
        """
        Creates simple features (Close Price) and Targets (Next Step Direction).
        Target = 1 if Close[t+1] > Close[t], else 0.
        """
        # Feature: Current Close
        # In a real scenario, we'd use many features. Here we just use Close for the mock.
        features = df['close'].values[:-1].reshape(-1, 1)
        
        # Target: 1 if Next Close > Current Close
        closes = df['close'].values
        targets = (closes[1:] > closes[:-1]).astype(int)
        
        return features, targets
