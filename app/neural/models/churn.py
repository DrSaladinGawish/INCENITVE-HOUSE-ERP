from sklearn.ensemble import RandomForestClassifier


class ChurnPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self._trained = False

    def train(self, features, labels):
        self.model.fit(features, labels)
        self._trained = True

    def predict(self, features):
        if not self._trained:
            return None, 0.0
        proba = self.model.predict_proba(features)
        confidence = float(proba.max(axis=1).mean())
        return self.model.predict(features).tolist(), confidence
