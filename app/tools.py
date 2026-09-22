"""Structured, historical investigation tools for the fraud analyst agent.

The dataset stores ``Time`` as seconds from the dataset start rather than a
wall-clock timestamp. Tool ``as_of`` datetimes are therefore converted to Unix
seconds before being compared with the stored value. Production deployments
should replace that conversion with an explicit dataset epoch.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd

from app.db_postgres import get_postgres_connection
from app.db_redis import get_redis_client
from app.layer1_rules import VELOCITY_KEY_PREFIX, VELOCITY_WINDOW_SECONDS
from app.layer3_model import CALIBRATED_MODEL_PATH, MODEL_FEATURES, explain_prediction
from app.lookup import get_card_history as lookup_card_history
from app.lookup import get_transaction_by_card_id


def _as_of_seconds(as_of: datetime) -> float:
    """Convert a timezone-aware investigation cutoff to comparable seconds."""
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    return as_of.timestamp()


def _mask(value: Any, visible: int = 4) -> str | None:
    """Mask an identifier while retaining a small suffix for analyst matching."""
    if value is None:
        return None
    text = str(value)
    if len(text) <= visible:
        return "*" * len(text)
    return "*" * (len(text) - visible) + text[-visible:]


def _mask_domain(value: Any) -> str | None:
    """Mask an email domain without exposing the original value."""
    if value is None:
        return None
    text = str(value)
    parts = text.split(".")
    if len(parts) > 1:
        return f"***.{parts[-1]}"
    return _mask(text)


def get_transaction(card_id: str, as_of: datetime) -> dict[str, Any]:
    """Get the latest transaction for a card strictly before ``as_of``.

    Card, device, and email-domain identifiers are masked before this result
    can be shown to an agent or analyst. Returns ``{"transaction": None}``
    when no historical transaction exists.
    """
    transaction = get_transaction_by_card_id(card_id, _as_of_seconds(as_of))
    if transaction is None:
        return {"transaction": None, "as_of": as_of.isoformat()}
    if float(transaction["time"]) >= _as_of_seconds(as_of):
        return {"transaction": None, "as_of": as_of.isoformat()}
    result = dict(transaction)
    result["card_id"] = _mask(result.get("card_id"))
    result["device_id"] = _mask(result.get("device_id"))
    result["purchaser_email_domain"] = _mask_domain(result.get("purchaser_email_domain"))
    result["recipient_email_domain"] = _mask_domain(result.get("recipient_email_domain"))
    return {"transaction": result, "as_of": as_of.isoformat()}


def get_card_history(
    card_id: str, as_of: datetime, window_hours: int = 24
) -> dict[str, Any]:
    """Return masked card history in the prior ``window_hours`` before ``as_of``."""
    cutoff = _as_of_seconds(as_of)
    rows = lookup_card_history(card_id, limit=1000, as_of=cutoff)
    lower_bound = cutoff - max(0, window_hours) * 60 * 60
    history = []
    for row in rows:
        if float(row["time"]) >= cutoff:
            continue
        if float(row["time"]) < lower_bound:
            continue
        item = dict(row)
        item["purchaser_email_domain"] = _mask_domain(item.get("purchaser_email_domain"))
        item["recipient_email_domain"] = _mask_domain(item.get("recipient_email_domain"))
        history.append(item)
    return {"card_id": _mask(card_id), "history": history, "as_of": as_of.isoformat()}


def get_device_history(device_id: str, as_of: datetime) -> dict[str, Any]:
    """List transactions and distinct cards seen on a device before ``as_of``."""
    connection = get_postgres_connection()
    if connection is None:
        return {"device_id": _mask(device_id), "transactions": [], "distinct_card_count": 0}
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT transaction_id, card_id, device_id, time, amount, decision, class_label "
                "FROM transactions WHERE device_id = %s AND time < %s "
                "ORDER BY time DESC, transaction_id DESC",
                (device_id, _as_of_seconds(as_of)),
            )
            columns = [description[0] for description in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cutoff = _as_of_seconds(as_of)
        rows = [row for row in rows if float(row["time"]) < cutoff]
        distinct_card_count = len({row["card_id"] for row in rows})
        for row in rows:
            row["card_id"] = _mask(row.get("card_id"))
            row["device_id"] = _mask(row.get("device_id"))
        return {
            "device_id": _mask(device_id),
            "transactions": rows,
            "distinct_card_count": distinct_card_count,
            "as_of": as_of.isoformat(),
        }
    finally:
        connection.close()


def get_email_domain_profile(domain: str, as_of: datetime) -> dict[str, Any]:
    """Return historical volume and fraud rate for an email domain before ``as_of``."""
    connection = get_postgres_connection()
    if connection is None:
        return {"domain": _mask_domain(domain), "transaction_count": 0, "fraud_rate": None}
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS transaction_count, "
                "AVG(class_label::double precision) AS fraud_rate "
                "FROM transactions WHERE time < %s "
                "AND (purchaser_email_domain = %s OR recipient_email_domain = %s)",
                (_as_of_seconds(as_of), domain, domain),
            )
            row = cursor.fetchone()
        return {
            "domain": _mask_domain(domain),
            "transaction_count": int(row[0] or 0),
            "fraud_rate": float(row[1]) if row[1] is not None else None,
            "as_of": as_of.isoformat(),
        }
    finally:
        connection.close()


def get_velocity(card_id: str, device_id: str, as_of: datetime) -> dict[str, Any]:
    """Read velocity evidence without adding an event to Redis.

    ``device_id`` is accepted for a consistent tool contract and future
    device-level velocity support; the current production rule is card-based.
    """
    client = get_redis_client()
    if client is None:
        return {"card_id": _mask(card_id), "count": 0, "flagged": False, "available": False}
    cutoff = _as_of_seconds(as_of)
    try:
        count = int(
            client.zcount(
                f"{VELOCITY_KEY_PREFIX}{card_id}",
                cutoff - VELOCITY_WINDOW_SECONDS,
                cutoff,
            )
        )
        return {
            "card_id": _mask(card_id),
            "device_id": _mask(device_id),
            "count": count,
            "flagged": count > 3,
            "available": True,
            "as_of": as_of.isoformat(),
        }
    finally:
        client.close()


def get_similar_transactions(
    transaction_features: Mapping[str, float], as_of: datetime, k: int = 5
) -> dict[str, Any]:
    """Return nearest historical transactions in ``Time``, ``Amount``, and V-space."""
    connection = get_postgres_connection()
    if connection is None:
        return {"transactions": [], "as_of": as_of.isoformat()}
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT transaction_id, card_id, device_id, time, amount, v_features, class_label "
                "FROM transactions WHERE time < %s",
                (_as_of_seconds(as_of),),
            )
            rows = cursor.fetchall()
    finally:
        connection.close()

    if not rows:
        return {"transactions": [], "as_of": as_of.isoformat()}
    feature_names = ["Time", "Amount"] + [f"V{i}" for i in range(1, 29)]
    target = np.array([float(transaction_features.get(name, 0.0)) for name in feature_names])
    candidates = []
    for row in rows:
        values = row[5] or {}
        vector = np.array([float(row[3]), float(row[4])] + [float(values.get(f"V{i}", 0.0)) for i in range(1, 29)])
        candidates.append((float(np.linalg.norm(vector - target)), row))
    candidates.sort(key=lambda item: item[0])
    results = []
    for distance, row in candidates[: max(0, k)]:
        results.append(
            {
                "transaction_id": row[0],
                "card_id": _mask(row[1]),
                "device_id": _mask(row[2]),
                "time": row[3],
                "amount": row[4],
                "class_label": row[6],
                "distance": distance,
            }
        )
    return {"transactions": results, "as_of": as_of.isoformat()}


def get_model_explanation(card_id: str) -> dict[str, Any]:
    """Return SHAP contributions for the latest stored transaction for a card."""
    transaction = get_transaction_by_card_id(card_id)
    if transaction is None:
        return {"card_id": _mask(card_id), "explanations": []}
    values = transaction.get("v_features") or {}
    row = {
        "Time": float(transaction["time"]),
        "Amount": float(transaction["amount"]),
        **{f"V{i}": float(values.get(f"V{i}", 0.0)) for i in range(1, 29)},
    }
    model = joblib.load(CALIBRATED_MODEL_PATH)
    contributions = explain_prediction(model, pd.Series(row), MODEL_FEATURES)
    return {
        "card_id": _mask(card_id),
        "explanations": [
            {"feature": item.split(": contributed", 1)[0], "text": item}
            for item in contributions
        ],
    }
