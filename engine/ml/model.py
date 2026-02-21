"""Isolation Forest for unsupervised anomaly detection. Per-user or global."""
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

MODEL_VERSION = "iforest_v1"


def _anomaly_to_risk(anomaly_score: float) -> float:
    """Map Isolation Forest anomaly score (-1 or 1 / decision_function) to 0-100 risk."""
    # decision_function: negative = more anomalous. We use score_samples -> lower = more anomalous.
    # IsolationForest score_samples: -0.5 ish = normal, lower = anomaly. Clamp and scale to 0-100.
    if np.isnan(anomaly_score):
        return 0.0
    # Typical range roughly [-0.6, -0.4]. More negative -> higher risk.
    low, high = -0.6, -0.2
    p = (anomaly_score - high) / (low - high) if low != high else 0.5
    p = max(0.0, min(1.0, p))
    return float(p * 100.0)


class AnomalyModel:
    def __init__(self, n_estimators: int = 100, contamination: float = 0.05):
        self.clf = IsolationForest(n_estimators=n_estimators, contamination=contamination, random_state=42)
        self._feature_names = None
        self._fitted = False

    def fit(self, X: np.ndarray) -> None:
        if X.shape[0] < 10:
            logger.warning("Not enough samples to fit Isolation Forest (%d)", X.shape[0])
            return
        self.clf.fit(X)
        self._fitted = True

    def score(self, X: np.ndarray) -> np.ndarray:
        """Anomaly score per sample (lower = more anomalous)."""
        if not self._fitted or X.shape[0] == 0:
            return np.array([0.0] * X.shape[0])
        return self.clf.score_samples(X)

    def risk_scores(self, X: np.ndarray) -> list[float]:
        """Return 0-100 risk per sample."""
        s = self.score(X)
        return [_anomaly_to_risk(float(s[i])) for i in range(len(s))]

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        import joblib
        joblib.dump({"clf": self.clf, "fitted": self._fitted}, path)

    @classmethod
    def load(cls, path: Path) -> "AnomalyModel":
        import joblib
        data = joblib.load(path)
        m = cls()
        m.clf = data["clf"]
        m._fitted = data.get("fitted", True)
        return m
