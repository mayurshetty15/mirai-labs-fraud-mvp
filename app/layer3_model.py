"""Layer 3 time-split fraud models and SHAP explanations."""

from pathlib import Path
from typing import Iterable

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from app.calibration import ProbabilityOnlyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    accuracy_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "creditcard_augmented.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "gbt_model.pkl"
CALIBRATED_MODEL_PATH = PROJECT_ROOT / "models" / "gbt_model_calibrated.pkl"
CALIBRATION_CURVE_PATH = PROJECT_ROOT / "models" / "calibration_curve.png"
BASELINE_FEATURES = ["Amount", "Time"]
MODEL_FEATURES = ["Time", "Amount"] + [f"V{i}" for i in range(1, 29)]
REQUIRED_COLUMNS = MODEL_FEATURES + ["Class", "card_id", "device_id"]

# Time and Amount are transaction-time inputs. V1-V28 are client-side PCA
# features; their leakage safety is inherited from client engineering and is
# not independently verifiable here.
FEATURE_NOTES = {
    "Time": "Transaction timestamp, available at authorization time.",
    "Amount": "Transaction amount, available at authorization time.",
    **{
        f"V{i}": (
            "Client-pre-anonymized PCA feature; leakage safety is inherited from "
            "client feature engineering and is not independently verifiable."
        )
        for i in range(1, 29)
    },
}


def load_and_split_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the CSV and reserve the latest 20 percent by Time for holdout."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    data = pd.read_csv(DATA_PATH).sort_values("Time").reset_index(drop=True)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")
    holdout_size = max(1, int(np.ceil(len(data) * 0.20)))
    return data.iloc[:-holdout_size].copy(), data.iloc[-holdout_size:].copy()


def _metrics(y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    """Calculate the requested holdout metrics at a 0.5 threshold."""
    predictions = probabilities >= 0.5
    return {
        "ROC-AUC": roc_auc_score(y_true, probabilities),
        "PR-AUC": average_precision_score(y_true, probabilities),
        "Precision": precision_score(y_true, predictions, zero_division=0),
        "Recall": recall_score(y_true, predictions, zero_division=0),
        "Accuracy": accuracy_score(y_true, predictions),
    }


def get_holdout_metrics() -> dict[str, float]:
    """Return saved-model metrics on the untouched, time-based holdout set."""
    _, holdout_data = load_and_split_data()
    raw_model = joblib.load(MODEL_PATH)
    calibrated_model = joblib.load(CALIBRATED_MODEL_PATH)
    raw_probabilities = raw_model.predict_proba(holdout_data[MODEL_FEATURES])[:, 1]
    calibrated_probabilities = calibrated_model.predict_proba(
        holdout_data[MODEL_FEATURES]
    )[:, 1]
    labels = holdout_data["Class"].astype(int)
    metrics = _metrics(labels, raw_probabilities)
    return {
        "roc_auc": float(metrics["ROC-AUC"]),
        "pr_auc": float(metrics["PR-AUC"]),
        "precision": float(metrics["Precision"]),
        "recall": float(metrics["Recall"]),
        "brier_score": float(brier_score_loss(labels, calibrated_probabilities)),
    }


def _train_lightgbm(
    x_train: pd.DataFrame, y_train: pd.Series, scale_pos_weight: float
) -> lgb.LGBMClassifier:
    """Train the configured LightGBM classifier."""
    model = lgb.LGBMClassifier(
        objective="binary",
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=63,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        verbosity=-1,
    )
    model.fit(x_train, y_train)
    return model


def explain_prediction(
    model: lgb.LGBMClassifier,
    transaction_row: pd.Series | pd.DataFrame,
    feature_names: Iterable[str],
) -> list[str]:
    """Return the five largest probability-space SHAP contributions."""
    feature_names = list(feature_names)
    row = (
        transaction_row[feature_names]
        if isinstance(transaction_row, pd.Series)
        else transaction_row[feature_names]
    )
    row_frame = pd.DataFrame([row]) if isinstance(row, pd.Series) else row
    background = getattr(model, "_shap_background", None)
    if background is None:
        background = row_frame
    tree_model = getattr(model, "calibrated_classifiers_", None)
    if tree_model:
        tree_model = tree_model[0].estimator
    if isinstance(tree_model, ProbabilityOnlyClassifier):
        tree_model = tree_model.estimator
    else:
        tree_model = model
    explainer = shap.TreeExplainer(
        tree_model,
        data=background,
        feature_perturbation="interventional",
        model_output="probability",
    )
    shap_values = explainer(row_frame)
    values = shap_values.values
    if values.ndim == 3:
        values = values[:, :, 1]
    contributions = values[0]
    top_indices = np.argsort(np.abs(contributions))[::-1][:5]
    return [
        f"{feature_names[index]}: contributed {contributions[index]:+.2f} to fraud score"
        for index in top_indices
    ]


def train_and_evaluate() -> tuple[lgb.LGBMClassifier, dict[str, dict[str, float]], pd.DataFrame]:
    """Train, calibrate, evaluate on the time holdout, and save both models."""
    train_data, holdout_data = load_and_split_data()
    x_train = train_data[MODEL_FEATURES]
    x_holdout = holdout_data[MODEL_FEATURES]
    y_train = train_data["Class"].astype(int)
    y_holdout = holdout_data["Class"].astype(int)
    negative_count = (y_train == 0).sum()
    positive_count = (y_train == 1).sum()
    if positive_count == 0:
        raise ValueError("Training data contains no fraudulent transactions.")
    scale_pos_weight = negative_count / positive_count

    baseline = make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
    )
    baseline.fit(train_data[BASELINE_FEATURES], y_train)
    baseline_probabilities = baseline.predict_proba(holdout_data[BASELINE_FEATURES])[:, 1]

    gbt_model = _train_lightgbm(x_train, y_train, scale_pos_weight)
    raw_holdout_probabilities = gbt_model.predict_proba(x_holdout)[:, 1]

    calibration_size = max(1, int(np.ceil(len(train_data) * 0.20)))
    calibration_data = train_data.iloc[-calibration_size:]
    x_calibration = calibration_data[MODEL_FEATURES]
    y_calibration = calibration_data["Class"].astype(int)
    isotonic_minimum_rows = 1000
    isotonic_minimum_positives = 100
    if (
        len(calibration_data) >= isotonic_minimum_rows
        and y_calibration.sum() >= isotonic_minimum_positives
    ):
        calibration_method = "isotonic"
        calibration_reason = (
            f"calibration slice has {len(calibration_data)} rows and "
            f"{int(y_calibration.sum())} fraud cases"
        )
    else:
        calibration_method = "sigmoid"
        calibration_reason = (
            f"calibration slice has {len(calibration_data)} rows and "
            f"{int(y_calibration.sum())} fraud cases; isotonic requires at least "
            f"{isotonic_minimum_rows} rows and {isotonic_minimum_positives} fraud cases"
        )
    calibrated_model = CalibratedClassifierCV(
        estimator=ProbabilityOnlyClassifier(gbt_model),
        method=calibration_method,
        cv="prefit",
    )
    calibrated_model.fit(x_calibration, y_calibration)
    calibrated_holdout_probabilities = calibrated_model.predict_proba(x_holdout)[:, 1]
    raw_metrics = _metrics(y_holdout, raw_holdout_probabilities)
    calibrated_metrics = _metrics(y_holdout, calibrated_holdout_probabilities)
    metrics = {
        "Baseline Logistic Regression": _metrics(y_holdout, baseline_probabilities),
        "LightGBM": raw_metrics,
        "LightGBM Calibrated": calibrated_metrics,
    }

    raw_brier = brier_score_loss(y_holdout, raw_holdout_probabilities)
    calibrated_brier = brier_score_loss(y_holdout, calibrated_holdout_probabilities)
    raw_fraction, raw_mean = calibration_curve(
        y_holdout, raw_holdout_probabilities, n_bins=10, strategy="quantile"
    )
    calibrated_fraction, calibrated_mean = calibration_curve(
        y_holdout, calibrated_holdout_probabilities, n_bins=10, strategy="quantile"
    )
    figure, axis = plt.subplots(figsize=(7, 6))
    axis.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
    axis.plot(raw_mean, raw_fraction, "o-", label="Raw LightGBM")
    axis.plot(calibrated_mean, calibrated_fraction, "o-", label="Calibrated LightGBM")
    axis.set_xlabel("Mean predicted probability")
    axis.set_ylabel("Actual fraud rate")
    axis.set_title("Fraud model calibration on time-based holdout")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Retain a small background sample so probability-space SHAP values are
    # available when the serialized model is later used for explanations.
    gbt_model._shap_background = x_train.sample(
        n=min(100, len(x_train)), random_state=42
    )
    calibrated_model._shap_background = gbt_model._shap_background
    joblib.dump(gbt_model, MODEL_PATH)
    joblib.dump(calibrated_model, CALIBRATED_MODEL_PATH)
    figure.savefig(CALIBRATION_CURVE_PATH, dpi=150)
    plt.close(figure)
    print(f"Training rows: {len(train_data)} | Holdout rows: {len(holdout_data)}")
    print(f"LightGBM scale_pos_weight: {scale_pos_weight:.4f}")
    print(
        f"Calibration method: {calibration_method} ({calibration_reason}); "
        f"calibration rows: {len(calibration_data)}"
    )
    print(
        f"Holdout Brier score: raw={raw_brier:.6f} | "
        f"calibrated={calibrated_brier:.6f}"
    )
    print(
        f"Holdout ROC-AUC: raw={raw_metrics['ROC-AUC']:.6f} | "
        f"calibrated={calibrated_metrics['ROC-AUC']:.6f}"
    )
    print(
        f"Holdout Recall: raw={raw_metrics['Recall']:.6f} | "
        f"calibrated={calibrated_metrics['Recall']:.6f}"
    )
    print("\nHoldout comparison (threshold=0.5)")
    print(f"{'Model':<30} {'ROC-AUC':>10} {'PR-AUC':>10} {'Precision':>10} {'Recall':>10}")
    for model_name, model_metrics in metrics.items():
        print(
            f"{model_name:<30} {model_metrics['ROC-AUC']:>10.4f} "
            f"{model_metrics['PR-AUC']:>10.4f} {model_metrics['Precision']:>10.4f} "
            f"{model_metrics['Recall']:>10.4f}"
        )
    print(f"\nSaved LightGBM model to {MODEL_PATH}")
    print(f"Saved calibrated model to {CALIBRATED_MODEL_PATH}")
    print(f"Saved calibration curve to {CALIBRATION_CURVE_PATH}")
    return gbt_model, metrics, holdout_data


if __name__ == "__main__":
    model, metrics, holdout = train_and_evaluate()
    fraud_rows = holdout[holdout["Class"].astype(int) == 1]
    if fraud_rows.empty:
        print("No fraud row exists in the holdout set for SHAP explanation.")
    else:
        random_fraud = fraud_rows.sample(n=1, random_state=42).iloc[0]
        print("\nSHAP explanation for one holdout fraud prediction:")
        for explanation in explain_prediction(model, random_fraud, MODEL_FEATURES):
            print(f"- {explanation}")
    print(f"\nFinal LightGBM holdout ROC-AUC: {metrics['LightGBM']['ROC-AUC']:.4f}")
