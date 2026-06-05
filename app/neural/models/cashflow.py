import numpy as np
from sklearn.linear_model import LinearRegression


class CashflowPredictor:
    def __init__(self):
        self.model = LinearRegression()
        self._trained = False

    def train(self, dates, balances):
        X = np.arange(len(balances)).reshape(-1, 1)
        y = np.array(balances, dtype=float)
        self.model.fit(X, y)
        self._trained = True

    def predict(self, forecast_days=30):
        if not self._trained:
            return None, 0.0
        last_idx = 0
        X_future = np.arange(last_idx + 1, last_idx + forecast_days + 1).reshape(-1, 1)
        preds = self.model.predict(X_future)
        confidence = max(0.0, min(1.0, self.model.score(
            np.arange(len(preds)).reshape(-1, 1), preds
        )))
        return preds.tolist(), confidence
