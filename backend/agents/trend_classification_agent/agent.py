import os
import joblib
import numpy as np
from ..base_agent import BaseAgent
from .data_loader import TrendDataLoader
from .model import TrendClassifier

class TrendClassificationAgent(BaseAgent):
    def __init__(self, model_path: str = "trend_xgb.json"):
        super().__init__()
        self.model_path = model_path
        self.model_wrapper = TrendClassifier()
        
    def train(self, data_path: str, **kwargs):
        print(f"TrendAgent: Loading data from {data_path}...")
        loader = TrendDataLoader(data_path)
        df = loader.load_data()
        X, y = loader.prepare_features_and_targets(df)
        
        print("TrendAgent: Training XGBoost...")
        self.model_wrapper.fit(X, y)
        print("TrendAgent: Training complete.")
        self.save(self.model_path)

    def predict(self, input_data):
        """
        Input: numpy array or list of features.
        Output: "BULLISH" or "BEARISH"
        """
        if isinstance(input_data, list):
            input_data = np.array(input_data)
        if len(input_data.shape) == 1:
            input_data = input_data.reshape(1, -1)
            
        prediction = self.model_wrapper.predict(input_data)
        return "BULLISH" if prediction[0] == 1 else "BEARISH"

    def save(self, path: str):
        # XGBoost prefers saving in JSON or UBJSON for compatibility
        self.model_wrapper.model.save_model(path)
        print(f"TrendAgent: Model saved to {path}")

    def load(self, path: str):
        if os.path.exists(path):
            self.model_wrapper.model.load_model(path)
            print(f"TrendAgent: Model loaded from {path}")
        else:
            print(f"TrendAgent: No model found at {path}")
