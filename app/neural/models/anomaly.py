from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    def __init__(self, contamination=0.05):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self._trained = False

    def train(self, features):
        self.model.fit(features)
        self._trained = True

    def predict(self, features):
        if not self._trained:
            return None, 0.0
        preds = self.model.predict(features)
        scores = self.model.score_samples(features)
        confidence = 1.0 - abs(preds).mean()
        return preds.tolist(), float(confidence)
