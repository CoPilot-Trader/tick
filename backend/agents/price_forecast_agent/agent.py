import torch
import torch.nn as nn
import torch.optim as optim
import os
from ..base_agent import BaseAgent
from .model import LSTMPredictor
from .data_loader import DataLoaderManager

class PriceForecastAgent(BaseAgent):
    def __init__(self, model_path: str = "lstm_model.pth", device: str = None):
        super().__init__()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if device is None else device
        self.model_path = model_path
        
        self.model = LSTMPredictor().to(self.device)
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
    def train(self, data_path: str, epochs: int = 10, batch_size: int = 32):
        print(f"PriceAgent: Training on device: {self.device}")
        
        loader_manager = DataLoaderManager(data_path)
        train_loader, test_loader = loader_manager.get_dataloaders(batch_size=batch_size)
        
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for sequences, targets in train_loader:
                sequences, targets = sequences.to(self.device), targets.to(self.device)
                
                # Forward pass
                outputs = self.model(sequences)
                loss = self.criterion(outputs.squeeze(), targets)
                
                # Backward and optimize
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            # avg_loss = total_loss / len(train_loader)
            # print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")
            
        print("PriceAgent: Training complete.")
        self.save(self.model_path)

    def predict(self, input_data):
        """
        Predicts the next value for a single sequence.
        Args:
            input_data: Numpy array or Tensor of shape (seq_len, input_dim) or (1, seq_len, input_dim)
        """
        self.model.eval()
        with torch.no_grad():
            sequence = input_data
            if not isinstance(sequence, torch.Tensor):
                sequence = torch.FloatTensor(sequence)
            
            if sequence.dim() == 2:
                sequence = sequence.unsqueeze(0) # Add batch dim
                
            sequence = sequence.to(self.device)
            prediction = self.model(sequence)
            return prediction.item()

    def save(self, path: str):
        torch.save(self.model.state_dict(), path)
        print(f"PriceAgent: Model saved to {path}")

    def load(self, path: str):
        if os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            self.model.eval()
            print(f"PriceAgent: Model loaded from {path}")
        else:
            print(f"PriceAgent: No saved model found at {path}")
