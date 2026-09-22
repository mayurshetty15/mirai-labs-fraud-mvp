"""End-to-end fraud scoring pipeline."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.layer1_rules import check_velocity
from app.layer2_graph import get_device_card_count, record_transaction_link
from app.layer3_model import CALIBRATED_MODEL_PATH, MODEL_FEATURES, explain_prediction
from app.layer4_anomaly import score_anomaly
from app.layer5_decision import combine_scores
from app.thresholds import GBT_REVIEW_THRESHOLD


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GBT_MODEL_PATH = CALIBRATED_MODEL_PATH
_GBT_MODEL_CACHE = None


def _feature_values(transaction: dict[str, Any]) -> dict[str, float]:
    """Normalize list or mapping V features into V1...V28 columns."""
    values = transaction.get("v_features", {})
    if isinstance(values, dict):
        normalized = {
            f"V{index}": float(values.get(f"V{index}", values.get(str(index), 0.0)))
            for index in range(1, 29)
        }
    else:
        if len(values) != 28:
            raise ValueError("v_features must contain exactly 28 values")
        normalized = {f"V{index}": float(value) for index, value in enumerate(values, 1)}
    return normalized


def _model_row(transaction: dict[str, Any]) -> pd.DataFrame:
    """Create the exact feature frame expected by the LightGBM model."""
    row = {
        "Time": float(transaction["time"]),
        "Amount": float(transaction["amount"]),
        **_feature_values(transaction),
    }
    return pd.DataFrame([[row[name] for name in MODEL_FEATURES]], columns=MODEL_FEATURES)


def generate_plain_summary(case_result: dict[str, Any]) -> str:
    """Create a specific, customer-ready explanation of the risk decision."""
    decision = str(case_result.get("decision", "review")).lower()
    decision_text = {
        "allow": "allowed",
        "review": "sent for review",
        "block": "blocked",
    }.get(decision, decision)
    rules_flag = bool(case_result.get("rules_flag"))
    graph_flag = bool(case_result.get("graph_flag"))
    anomaly_flag = bool(case_result.get("anomaly_flag"))
    gbt_score = float(case_result.get("gbt_score", 0.0))
    velocity_count = int(case_result.get("velocity_count", 0))
    device_card_count = int(case_result.get("device_card_count", 0))
    anomaly_score = case_result.get("anomaly_score")
    confidence = max(0, min(100, round(gbt_score * 100)))
    confidence_word = (
        "elevated fraud risk"
        if gbt_score >= GBT_REVIEW_THRESHOLD
        else "low fraud risk"
    )

    signals = []
    if rules_flag:
        signals.append(
            (
                f"the card was used {velocity_count} times within the last 60 seconds, "
                "which matches card testing, where a stolen card is tested with rapid transactions",
                "",
            )
        )
    if graph_flag:
        signals.append(
            (
                f"this device has been used with {device_card_count} different cards, "
                "which is unusual for a single legitimate customer",
                f"This device has been used with {device_card_count} different cards.",
            )
        )
    if anomaly_flag:
        signals.append(
            (
                "the transaction's behavior falls significantly outside the normal range",
                (
                    f"The transaction's anomaly score was {float(anomaly_score):.3f}; "
                    "lower scores indicate behavior farther from normal."
                    if anomaly_score is not None
                    else "The transaction's behavior fell significantly outside the normal range."
                ),
            )
        )
    if gbt_score >= GBT_REVIEW_THRESHOLD:
        signals.append(
            (
                f"the transaction's characteristics matching historical fraud patterns "
                f"with a {gbt_score:.3%} calibrated model probability",
                (
                    f"The calibrated risk model assigns this transaction a {gbt_score:.3%} "
                    "fraud probability based on patterns seen in confirmed fraud cases."
                ),
            )
        )

    primary_signal = signals[0] if signals else None
    if primary_signal:
        opening_reason = primary_signal[0]
        opening = f"This transaction is being {decision_text} primarily because {opening_reason}."
    else:
        opening = f"This transaction is being {decision_text} because no significant fraud signal was detected."

    clean_checks = []
    if not rules_flag:
        clean_checks.append("No unusual card velocity was detected")
    if not graph_flag:
        clean_checks.append("This device has not been linked to other cards")
    if not anomaly_flag:
        clean_checks.append("No unusual account or session behavior was detected")
    clean_sentence = (
        " ".join(f"{check}." for check in clean_checks)
        if clean_checks
        else "All behavioral checks raised a concern."
    )

    secondary_signals = [signal[1] for signal in signals[1:] if signal[1]]
    secondary_sentence = ""
    if secondary_signals:
        secondary_sentence = "Additional concerns were also found. " + " ".join(secondary_signals)

    action = (
        "If you did not make this transaction yourself, please report your card as compromised. "
        "If you did make it, please contact us to verify your identity so we can release the hold."
    )

    return " ".join(
        part
        for part in (
            opening,
            clean_sentence,
            secondary_sentence,
            f"The system is {confidence_word} ({confidence}%) in this risk assessment.",
            action,
        )
        if part
    )


def run_pipeline(
    transaction: dict[str, Any],
    include_external_layers: bool = True,
    include_explanation: bool = True,
    model: Any = None,
    precomputed_gbt_score: float | None = None,
) -> dict[str, Any]:
    """Run fraud layers and return a resilient scoring result.

    Batch pre-scoring can disable live Redis/Neo4j checks because those
    stateful layers are evaluated again when an analyst opens a case.
    """
    errors: list[str] = []
    rules_flag = False
    graph_flag = False
    anomaly_flag = False
    anomaly_score = None
    velocity_count = 0
    device_card_count = 0
    gbt_score = 0.0
    model_score_available = False
    top_features: list[str] = []
    model_row = None

    if include_external_layers:
        try:
            rules_flag, velocity_count = check_velocity(
                transaction["card_id"], transaction["time"]
            )
        except Exception as error:
            errors.append(f"Layer 1 skipped: {error}")

        try:
            record_transaction_link(transaction["device_id"], transaction["card_id"])
            card_count = get_device_card_count(transaction["device_id"])
            device_card_count = card_count or 0
            graph_flag = card_count is not None and card_count > 3
        except Exception as error:
            errors.append(f"Layer 2 skipped: {error}")

    try:
        if not GBT_MODEL_PATH.exists():
            raise FileNotFoundError(f"GBT model not found: {GBT_MODEL_PATH}")
        global _GBT_MODEL_CACHE
        if model is None:
            if _GBT_MODEL_CACHE is None:
                _GBT_MODEL_CACHE = joblib.load(GBT_MODEL_PATH)
            model = _GBT_MODEL_CACHE
        if precomputed_gbt_score is not None:
            gbt_score = float(precomputed_gbt_score)
            model_score_available = True
        else:
            model_row = _model_row(transaction)
            gbt_score = float(model.predict_proba(model_row)[0, 1])
            model_score_available = True
            if include_explanation:
                top_features = explain_prediction(model, model_row.iloc[0], MODEL_FEATURES)
    except Exception as error:
        errors.append(f"Layer 3 skipped: {error}")

    try:
        anomaly_input = {
            "Time": transaction["time"],
            "Amount": transaction["amount"],
            **_feature_values(transaction),
        }
        anomaly_flag, anomaly_score = score_anomaly(anomaly_input)
    except Exception as error:
        errors.append(f"Layer 4 skipped: {error}")

    decision_result = combine_scores(rules_flag, graph_flag, gbt_score)
    reason = decision_result["reason"]
    if errors:
        reason = f"{reason}. " + " ".join(errors)

    result = {
        **decision_result,
        "anomaly_flag": anomaly_flag,
        "anomaly_score": anomaly_score,
        "velocity_count": velocity_count,
        "device_card_count": device_card_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_input_available": model_row is not None,
        "model_score_available": model_score_available,
    }
    result["plain_summary"] = generate_plain_summary(result)
    return result
