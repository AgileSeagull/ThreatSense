"""Isolation Forest for unsupervised anomaly detection. Per-user or global."""
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

MODEL_VERSION = "iforest_v1"


def _anomaly_to_risk(anomaly_score: float, offset: float = -0.5) -> float:
    """Map Isolation Forest score_samples to 0-100 risk using the model's own offset_.

    IsolationForest.offset_ is the decision threshold: scores above it are inliers
    (normal), scores below it are outliers (anomalous). Using offset_ as the pivot
    means normal training data always lands near 0 regardless of the dataset.
    """
    if np.isnan(anomaly_score):
        return 0.0
    if anomaly_score >= offset:
        # Inlier — well within normal range.
        return 0.0
    # Outlier — scale distance below offset linearly to 10-100.
    # 0.25 units below offset = fully anomalous (risk 100).
    distance = offset - anomaly_score
    p = min(1.0, distance / 0.25)
    return float(10.0 + p * 90.0)


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
        offset = float(self.clf.offset_) if self._fitted else -0.5
        return [_anomaly_to_risk(float(s[i]), offset) for i in range(len(s))]

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
