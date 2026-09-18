"""Score every unscored PostgreSQL transaction before analyst review."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd

from app.lookup import get_unscored_transactions, update_scores
from app.layer3_model import MODEL_FEATURES
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


def score_batch() -> int:
    rows = get_unscored_transactions()
    print(f"Found {len(rows)} unscored transaction(s).")
    if not rows:
        print("No scoring needed at this time.")
        return 0
    scored = 0
    pending_updates = []
    model = joblib.load(PROJECT_ROOT / "models" / "gbt_model.pkl")
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
                update_scores(pending_updates)
                pending_updates.clear()
            scored += 1
            print(
                f"[{index}/{len(rows)}] transaction_id={row['transaction_id']} "
                f"gbt_score={result['gbt_score']:.4f} decision={result['decision']}"
            )
        except Exception as error:
            print(f"[{index}/{len(rows)}] failed: {error}")
    update_scores(pending_updates)
    print(f"Batch scoring complete: {scored}/{len(rows)} transaction(s) scored.")
    return scored


if __name__ == "__main__":
    score_batch()
