import os
import numpy as np
from backend.agents.price_forecast_agent import PriceForecastAgent
from backend.agents.trend_classification_agent import TrendClassificationAgent
from backend.agents.support_resistance_agent import SupportResistanceAgent

def test_unified_system():
    print("=== UNIFIED PREDICTION SYSTEM VERIFICATION ===")
    
    # DATA_PATH = "backend/data/refined_sample_1000.json"
    # Robust path construction relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(script_dir, "backend", "data", "refined_sample_1000.json")
    
    if not os.path.exists(DATA_PATH):
        print(f"CRITICAL: Data file missing at {DATA_PATH}")
        return

    # --- Configuration Report ---
    print("\n--- CONFIGURATION & DATA ---")
    print(f"Dataset: {os.path.basename(DATA_PATH)}")
    print("Ticker:  SAMPLE_DATA (inferred from filename 'refined_sample_1000.json')")
    print("\n[Features Used by Models]")
    print("1. PriceForecastAgent:      ['close'] (Univariate Time-Series)")
    print("2. TrendClassificationAgent:['close'] (Derived: Close[t] vs Close[t-1])")
    print("3. SupportResistanceAgent:  ['high', 'low'] (Local Extrema)")
    print("----------------------------")

    # --- 1. Price Forecast Agent ---
    print("\n[1] Testing PriceForecastAgent...")
    try:
        price_agent = PriceForecastAgent(model_path="price_lstm.pth")
        price_agent.train(data_path=DATA_PATH, epochs=1) # Minimal training
        
        dummy_seq = np.random.rand(60, 1) # 60 timestamps, 1 feature
        pred = price_agent.predict(dummy_seq)
        print(f"    Prediction: {pred} (Type: {type(pred)})")
        print("    >> SUCCESS")
    except Exception as e:
        print(f"    >> FAILED: {e}")

    # --- 2. Trend Classification Agent ---
    print("\n[2] Testing TrendClassificationAgent...")
    try:
        trend_agent = TrendClassificationAgent(model_path="trend_xgb.json")
        trend_agent.train(data_path=DATA_PATH)
        
        dummy_input = np.random.rand(1, 1) # 1 sample, 1 feature (Close)
        trend = trend_agent.predict(dummy_input)
        print(f"    Trend: {trend} (Type: {type(trend)})")
        print("    >> SUCCESS")
    except Exception as e:
        print(f"    >> FAILED: {e}")

    # --- 3. Support/Resistance Agent ---
    print("\n[3] Testing SupportResistanceAgent...")
    try:
        sr_agent = SupportResistanceAgent(window=10)
        sr_agent.train(data_path=DATA_PATH) # Pre-calc levels
        
        levels = sr_agent.predict(None) # Input ignored
        print(f"    Levels Found: {len(levels)} (First 5: {levels[:5]})")
        print("    >> SUCCESS")
    except Exception as e:
        print(f"    >> FAILED: {e}")

    print("\n=== SYSTEM VERIFICATION COMPLETE ===")
    
    # Cleanup artifacts
    for f in ["price_lstm.pth", "trend_xgb.json", "sr_levels.json"]:
        if os.path.exists(f):
            try:
               os.remove(f)
            except:
                pass


if __name__ == "__main__":
    test_unified_system()
