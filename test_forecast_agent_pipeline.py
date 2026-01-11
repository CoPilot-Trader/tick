import os
import torch
import numpy as np
import traceback
from backend.agents.price_forecast_agent import PriceForecastAgent

def test_pipeline():
    print("=== Starting Price Forecast Agent Pipeline Verification ===")
    
    # 0. Setup Paths
    # Adjust this path if necessary to point correctly relative to where you run the script
    DATA_PATH = "backend/data/refined_sample_1000.json"
    MODEL_PATH = "lstm_test_model.pth"
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    # 1. Initialize Agent
    print("\n1. Initializing Agent...")
    agent = PriceForecastAgent(model_path=MODEL_PATH)
    print("Agent initialized.")

    # 2. Train (Simulate 1 epoch for speed)
    print("\n2. Training Agent (1 Epoch)...")
    try:
        agent.train(data_path=DATA_PATH, epochs=1, batch_size=16)
        print("Training successful.")
    except Exception as e:
        print(f"Training failed: {e}")
        traceback.print_exc()
        return

    # 3. Predict (Inference)
    print("\n3. Testing Inference...")
    try:
        # Create a dummy sequence (60 timesteps, 1 feature)
        dummy_seq = np.random.rand(60, 1)
        prediction = agent.predict(dummy_seq)
        
        print(f"Input shape: {dummy_seq.shape}")
        print(f"Prediction result: {prediction}")
        print(f"Prediction type: {type(prediction)}")
        
        assert isinstance(prediction, float), "Prediction should be a float"
        print("Inference verification successful.")
        
    except Exception as e:
        print(f"Inference failed: {e}")
        return

    print("\n=== Pipeline Verification Complete: SUCCESS ===")
    
    # Cleanup
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)

if __name__ == "__main__":
    test_pipeline()
