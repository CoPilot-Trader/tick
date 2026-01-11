import json
import torch
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, List

class StockDataset(Dataset):
    def __init__(self, sequences, targets):
        self.sequences = sequences
        self.targets = targets

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return torch.tensor(self.sequences[idx], dtype=torch.float32), torch.tensor(self.targets[idx], dtype=torch.float32)

class DataLoaderManager:
    def __init__(self, data_path: str, sequence_length: int = 60, train_split: float = 0.8):
        self.data_path = data_path
        self.sequence_length = sequence_length
        self.train_split = train_split
        self.scaler_min = 0
        self.scaler_max = 1
        
    def load_data(self):
        """Loads data from JSON and returns pandas DataFrame."""
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        # Ensure timestamp is datetime and sort
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        return df

    def preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, float, float]:
        """Extracts Close price and normalizes it."""
        prices = df['close'].values.astype(float)
        
        # Simple MinMax Scaling
        self.scaler_min = np.min(prices)
        self.scaler_max = np.max(prices)
        
        # Avoid division by zero
        if self.scaler_max == self.scaler_min:
             normalized_prices = np.zeros_like(prices)
        else:
            normalized_prices = (prices - self.scaler_min) / (self.scaler_max - self.scaler_min)
            
        return normalized_prices, self.scaler_min, self.scaler_max

    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Creates sequences for LSTM input."""
        sequences = []
        targets = []
        for i in range(len(data) - self.sequence_length):
            seq = data[i:i+self.sequence_length]
            target = data[i+self.sequence_length]
            sequences.append(seq)
            targets.append(target)
        return np.array(sequences), np.array(targets)

    def get_dataloaders(self, batch_size: int = 32) -> Tuple[DataLoader, DataLoader]:
        """Orchestrates loading, processing, and DataLoader creation."""
        df = self.load_data()
        normalized_data, _, _ = self.preprocess_data(df)
        X, y = self.create_sequences(normalized_data)

        # Reshape X to (samples, seq_len, features) implementation assumes 1 feature (Close)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Train/Test Split
        split_idx = int(len(X) * self.train_split)
        
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        train_dataset = StockDataset(X_train, y_train)
        test_dataset = StockDataset(X_test, y_test)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        return train_loader, test_loader
