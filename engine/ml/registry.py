"""Model registry: global Isolation Forest. Lazy train from DB when enough events."""
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from engine.ml.features import extract_features, get_feature_names
from engine.ml.model import AnomalyModel, MODEL_VERSION

logger = logging.getLogger(__name__)

GLOBAL_MODEL_FILENAME = "global_model.joblib"


class ModelRegistry:
    def __init__(self, model_dir: str = "data/models", min_samples_to_fit: int = 30):
        self.model_dir = Path(model_dir)
        self.min_samples = min_samples_to_fit
        self._global_model: Optional[AnomalyModel] = None
        self._global_fitted = False
        self._training_mean: Optional[np.ndarray] = None
        self._training_std: Optional[np.ndarray] = None

    def _global_model_path(self) -> Path:
        return self.model_dir / GLOBAL_MODEL_FILENAME

    def load_global(self) -> bool:
        """Load global model and training stats from disk. Returns True if loaded successfully."""
        path = self._global_model_path()
        if not path.exists():
            return False
        try:
            data = joblib.load(path)
            if data.get("version") != MODEL_VERSION:
                logger.warning(
                    "Saved model version %s != current %s; ignoring persisted model",
                    data.get("version"),
                    MODEL_VERSION,
                )
                return False
            m = AnomalyModel()
            m.clf = data["clf"]
            m._fitted = data.get("fitted", True)
            self._global_model = m
            self._global_fitted = True
            self._training_mean = data.get("training_mean")
            self._training_std = data.get("training_std")
            logger.info("Loaded global anomaly model from %s", path)
            return True
        except Exception as e:
            logger.warning("Failed to load global model from %s: %s", path, e)
            return False

    def save_global(self) -> None:
        """Persist global model and training stats to disk. No-op if not fitted."""
        if not self._global_fitted or self._global_model is None:
            return
        path = self._global_model_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(
                {
                    "version": MODEL_VERSION,
                    "clf": self._global_model.clf,
                    "fitted": self._global_model._fitted,
                    "training_mean": self._training_mean,
                    "training_std": self._training_std,
                },
                path,
            )
            logger.info("Saved global anomaly model to %s", path)
        except Exception as e:
            logger.warning("Failed to save global model to %s: %s", path, e)

    def fit_global(self, events: list[dict]) -> bool:
        """Fit global model on list of event dicts. Returns True if fitted."""
        if len(events) < self.min_samples:
            return False
        X = np.array([extract_features(e) for e in events])
        if self._global_model is None:
            self._global_model = AnomalyModel()
        self._global_model.fit(X)
        self._global_fitted = True
        self._training_mean = X.mean(axis=0)
        self._training_std = X.std(axis=0)
        self._training_std[self._training_std == 0] = 1.0
        return True

    def score_event(self, event: dict) -> tuple[float, list[str]]:
        """
        Score a single event. Returns (risk_score, contributing_factors).
        Factors describe which features deviate most from the training baseline.
        """
        if self._global_model is None or not self._global_fitted:
            return 0.0, []
        x = extract_features(event).reshape(1, -1)
        risks = self._global_model.risk_scores(x)
        risk = float(risks[0]) if risks else 0.0
        factors = self._compute_factors(event, x[0])
        return risk, factors

    def _compute_factors(self, event: dict, features: np.ndarray) -> list[str]:
        """Identify which features deviate most from training mean and describe them."""
        if self._training_mean is None:
            return []

        names = get_feature_names()
        z_scores = np.abs((features - self._training_mean) / self._training_std)
        top_indices = np.argsort(z_scores)[::-1]

        payload = event.get("payload") or {}
        source = event.get("source", "")
        user = event.get("user", "unknown")

        factors: list[str] = []
        for idx in top_indices[:3]:
            if z_scores[idx] < 0.5:
                break
            name = names[idx] if idx < len(names) else f"feature_{idx}"
            desc = self._describe_factor(name, features[idx], event, payload, source, user)
            if desc:
                factors.append(desc)

        return factors if factors else [f"anomaly_model_{MODEL_VERSION}"]

    @staticmethod
    def _describe_factor(
        name: str, value: float, event: dict, payload: dict, source: str, user: str,
    ) -> str:
        ts = event.get("timestamp")
        hour = None
        if hasattr(ts, "hour"):
            hour = ts.hour
        elif isinstance(ts, str):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hour = dt.hour
            except Exception:
                pass

        if name == "hour" and hour is not None:
            if hour < 6 or hour >= 22:
                return f"unusual_time_of_day ({hour:02d}:00 UTC)"
            return f"activity_time ({hour:02d}:00 UTC)"
        if name == "dow":
            return "unusual_day_of_week"
        if name == "source":
            return f"event_type_{source}"
        if name == "auth_action_bucket":
            action = payload.get("action", "unknown")
            success = payload.get("success")
            if success is False:
                return f"auth_failure ({action})"
            return f"auth_action ({action})"
        if name == "user_bucket":
            return f"uncommon_user ({user})"
        if name == "machine_bucket":
            return f"uncommon_machine ({event.get('machine_id', 'unknown')})"
        if name == "exe_bucket":
            exe = payload.get("exe", "unknown")
            return f"unusual_executable ({exe})"
        if name == "command_hash_bucket":
            return "unusual_command_hash"
        if name == "command_length_norm":
            length = payload.get("command_length", 0)
            return f"unusual_command_length ({length} chars)"
        return name
