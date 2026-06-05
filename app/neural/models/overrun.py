from sklearn.ensemble import GradientBoostingRegressor


class OverrunPredictor:
    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self._trained = False

    def train(self, features, actual_costs):
        self.model.fit(features, actual_costs)
        self._trained = True

    def predict(self, features):
        if not self._trained:
            return None, 0.0
        preds = self.model.predict(features)
        confidence = max(0.0, min(1.0, self.model.score(features, preds)))
        return preds.tolist(), confidence
