from xgboost import XGBClassifier
import joblib
import os

class TrendClassifier:
    def __init__(self, n_estimators=100, learning_rate=0.1):
        self.model = XGBClassifier(
            n_estimators=n_estimators, 
            learning_rate=learning_rate,
            eval_metric='logloss'
        )
        
    def fit(self, X, y):
        self.model.fit(X, y)
        
    def predict(self, X):
        return self.model.predict(X)
        
    def predict_proba(self, X):
        return self.model.predict_proba(X)
