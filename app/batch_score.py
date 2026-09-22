"""Score every unscored PostgreSQL transaction before analyst review."""

from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd

from app.db_postgres import get_postgres_connection
from app.lookup import get_unscored_transactions
from app.layer3_model import CALIBRATED_MODEL_PATH, MODEL_FEATURES
from app.pipeline import run_pipeline


def _pipeline_transaction(row: dict) -> dict:
    """Convert a PostgreSQL row into the pipeline input shape."""
    return {
        "card_id": row["card_id"],
        "device_id": row["device_id"],
        "time": row["time"],
        "amount": row["amount"],
        "v_features": row["v_features"],
        "purchaser_email_domain": row["purchaser_email_domain"],
        "recipient_email_domain": row["recipient_email_domain"],
    }


def _flush_updates(connection, pending_updates: list[tuple[int, float, str]]) -> None:
    if not pending_updates:
        return
    with connection.cursor() as cursor:
        cursor.executemany(
            "UPDATE transactions SET gbt_score = %s, decision = %s "
            "WHERE transaction_id = %s",
            [
                (score, decision, transaction_id)
                for transaction_id, score, decision in pending_updates
            ],
        )
    connection.commit()


def score_batch() -> int:
    started_at = time.perf_counter()
    rows = get_unscored_transactions()
    print(f"Found {len(rows)} unscored transaction(s).")
    if not rows:
        print("No scoring needed at this time.")
        return 0
    scored = 0
    pending_updates = []
    model = joblib.load(CALIBRATED_MODEL_PATH)
    model_rows = []
    for row in rows:
        values = row["v_features"]
        model_rows.append(
            {
                "Time": float(row["time"]),
                "Amount": float(row["amount"]),
                **{f"V{i}": float(values.get(f"V{i}", 0.0)) for i in range(1, 29)},
            }
        )
    probabilities = model.predict_proba(pd.DataFrame(model_rows)[MODEL_FEATURES])[:, 1]
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable for batch score updates.")

    failures: list[str] = []
    try:
        for index, row in enumerate(rows, start=1):
            try:
                result = run_pipeline(
                    _pipeline_transaction(row),
                    include_external_layers=False,
                    include_explanation=False,
                    precomputed_gbt_score=float(probabilities[index - 1]),
                )
                pending_updates.append(
                    (row["transaction_id"], result["gbt_score"], result["decision"])
                )
                if len(pending_updates) >= 250:
                    _flush_updates(connection, pending_updates)
                    pending_updates.clear()
                scored += 1
                print(
                    f"[{index}/{len(rows)}] transaction_id={row['transaction_id']} "
                    f"gbt_score={result['gbt_score']:.4f} decision={result['decision']}"
                )
            except Exception as error:
                failures.append(f"transaction_id={row['transaction_id']}: {error}")
                print(f"[{index}/{len(rows)}] failed: {error}")
        _flush_updates(connection, pending_updates)
        if failures:
            raise RuntimeError(
                f"Batch scoring failed for {len(failures)} transaction(s): "
                + "; ".join(failures[:5])
            )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    duration = time.perf_counter() - started_at
    print(
        f"Batch scoring complete: {scored}/{len(rows)} transaction(s) scored "
        f"in {duration:.2f}s ({scored / duration:.2f} rows/s)."
    )
    return scored


if __name__ == "__main__":
    score_batch()
