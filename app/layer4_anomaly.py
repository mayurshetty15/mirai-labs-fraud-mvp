"""Layer 4 anomaly detection using an IsolationForest."""

import json
from pathlib import Path
import sys
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Support both ``python -m app.layer4_anomaly`` and the requested direct form.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.layer3_model import load_and_split_data


ANOMALY_MODEL_PATH = PROJECT_ROOT / "models" / "anomaly_model.pkl"
ANOMALY_THRESHOLD_PATH = PROJECT_ROOT / "models" / "anomaly_threshold.json"
ANOMALY_FEATURES = ["Time", "Amount", "activity_magnitude"]
_ANOMALY_MODEL_CACHE = None
_ANOMALY_THRESHOLD_CACHE = None


def _to_feature_frame(transaction_data: pd.DataFrame | pd.Series | dict[str, Any]) -> pd.DataFrame:
    """Build the three numeric anomaly features from a row-like value."""
    if isinstance(transaction_data, pd.DataFrame):
        frame = transaction_data.copy()
    elif isinstance(transaction_data, pd.Series):
        frame = transaction_data.to_frame().T
    else:
        frame = pd.DataFrame([transaction_data])

    v_columns = [f"V{i}" for i in range(1, 29)]
    missing = [column for column in ["Time", "Amount", *v_columns] if column not in frame]
    if missing:
        raise ValueError(f"Transaction is missing anomaly features: {missing}")
    features = pd.DataFrame(index=frame.index)
    features["Time"] = pd.to_numeric(frame["Time"])
    features["Amount"] = pd.to_numeric(frame["Amount"])
    features["activity_magnitude"] = frame[v_columns].abs().sum(axis=1)
    return features[ANOMALY_FEATURES].astype(float)


def fit_and_save_anomaly_model() -> IsolationForest:
    """Train IsolationForest on the Layer 3 training split and save its threshold."""
    train_data, _ = load_and_split_data()
    training_features = _to_feature_frame(train_data)
    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(training_features)
    training_scores = model.decision_function(training_features)
    threshold = float(np.percentile(training_scores, 5))

    ANOMALY_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ANOMALY_MODEL_PATH)
    ANOMALY_THRESHOLD_PATH.write_text(
        json.dumps(
            {
                "threshold": threshold,
                "percentile": 5,
                "features": ANOMALY_FEATURES,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Anomaly model saved to {ANOMALY_MODEL_PATH}")
    print(f"Anomaly threshold (5th percentile): {threshold:.6f}")
    return model


def score_anomaly(transaction_row: pd.Series | dict[str, Any]) -> tuple[bool, float]:
    """Return ``(is_anomalous, raw_decision_function_score)`` for one transaction."""
    if not ANOMALY_MODEL_PATH.exists() or not ANOMALY_THRESHOLD_PATH.exists():
        raise FileNotFoundError(
            "Anomaly model files are missing. Run fit_and_save_anomaly_model() first."
        )

    global _ANOMALY_MODEL_CACHE, _ANOMALY_THRESHOLD_CACHE
    if _ANOMALY_MODEL_CACHE is None:
        _ANOMALY_MODEL_CACHE = joblib.load(ANOMALY_MODEL_PATH)
    if _ANOMALY_THRESHOLD_CACHE is None:
        _ANOMALY_THRESHOLD_CACHE = json.loads(
            ANOMALY_THRESHOLD_PATH.read_text(encoding="utf-8")
        )
    model = _ANOMALY_MODEL_CACHE
    threshold_data = _ANOMALY_THRESHOLD_CACHE
    score = float(model.decision_function(_to_feature_frame(transaction_row))[0])
    return score < float(threshold_data["threshold"]), score


if __name__ == "__main__":
    fit_and_save_anomaly_model()
    _, holdout_data = load_and_split_data()
    holdout_row = holdout_data.iloc[0]
    anomaly_flag, anomaly_score = score_anomaly(holdout_row)
    print(
        "Holdout anomaly test: "
        f"flagged={anomaly_flag}, raw_score={anomaly_score:.6f}"
    )
