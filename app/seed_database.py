"""Seed PostgreSQL with a representative sample of transaction data."""

from pathlib import Path
import sys

import pandas as pd
from psycopg2.extras import Json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db_postgres import get_postgres_connection

DATA_PATH = PROJECT_ROOT / "data" / "creditcard_augmented.csv"
V_COLUMNS = [f"V{i}" for i in range(1, 29)]
SEED_CARD_LIMIT = 400
SEED_ROW_LIMIT = 25_000
HIGH_HISTORY_CARD_TARGET = 200
FRAUD_HISTORY_CARD_TARGET = 150
DEMO_CARD_IDS = ("card_b39a7255",)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    card_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    time DOUBLE PRECISION NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    v_features JSONB NOT NULL,
    purchaser_email_domain TEXT,
    recipient_email_domain TEXT,
    class_label INTEGER NOT NULL,
    gbt_score DOUBLE PRECISION,
    decision TEXT,
    reviewed_by_human BOOLEAN NOT NULL DEFAULT FALSE
)
"""

INSERT_SQL = """
INSERT INTO transactions (
    card_id, device_id, time, amount, v_features,
    purchaser_email_domain, recipient_email_domain, class_label
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def _select_cards(
    data: pd.DataFrame,
    card_limit: int,
    row_limit: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select complete card histories using depth, fraud, and row-budget signals."""
    card_stats = data.groupby("card_id", sort=False).agg(
        transaction_count=("card_id", "size"),
        has_fraud=("Class", "max"),
    )
    high_history = card_stats.sort_values(
        ["transaction_count", "has_fraud"], ascending=[False, False]
    ).head(HIGH_HISTORY_CARD_TARGET)
    fraud_history = card_stats[card_stats["has_fraud"] == 1].sort_values(
        ["transaction_count", "has_fraud"], ascending=[False, False]
    ).head(FRAUD_HISTORY_CARD_TARGET)

    selected_ids: list[str] = [
        card_id
        for card_id in DEMO_CARD_IDS
        if card_id in card_stats.index
        and int(card_stats.loc[card_id, "transaction_count"]) <= row_limit
    ]
    for card_group in (
        high_history,
        fraud_history,
        card_stats.sort_values("transaction_count", ascending=False),
    ):
        for card_id in card_group.index:
            card_id = str(card_id)
            if card_id in selected_ids or len(selected_ids) >= card_limit:
                continue
            projected_rows = int(card_stats.loc[card_id, "transaction_count"])
            current_rows = sum(int(card_stats.loc[item, "transaction_count"]) for item in selected_ids)
            if current_rows + projected_rows > row_limit:
                continue
            selected_ids.append(card_id)

    selected = data[data["card_id"].astype(str).isin(selected_ids)].copy()
    return selected, card_stats.loc[selected_ids]


def seed_database(
    card_limit: int = SEED_CARD_LIMIT,
    row_limit: int = SEED_ROW_LIMIT,
) -> int:
    """Create the table and seed complete histories for a deliberate card sample."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("Could not connect to PostgreSQL for seeding.")

    try:
        data = pd.read_csv(DATA_PATH)
        data["card_id"] = data["card_id"].astype(str)
        data, selected_stats = _select_cards(data, card_limit, row_limit)
        rows = []
        for row in data.to_dict(orient="records"):
            v_features = {column: float(row[column]) for column in V_COLUMNS}
            rows.append(
                (
                    str(row["card_id"]),
                    str(row["device_id"]),
                    float(row["Time"]),
                    float(row["Amount"]),
                    Json(v_features),
                    str(row["purchaser_email_domain"]),
                    str(row["recipient_email_domain"]),
                    int(row["Class"]),
                )
            )
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_TABLE_SQL)
                cursor.execute("TRUNCATE TABLE transactions RESTART IDENTITY")
                cursor.executemany(INSERT_SQL, rows)
        counts = data.groupby("card_id").size()
        fraud_cards = int(selected_stats["has_fraud"].sum())
        minimal_cards = int((counts == 1).sum())
        print("\nDatabase seed summary")
        print("---------------------")
        print(f"Seeded rows:              {len(rows):,}")
        print(f"Unique cards:             {counts.size:,}")
        print(f"Cards with fraud history: {fraud_cards:,}")
        print(f"Min transactions/card:    {int(counts.min()) if not counts.empty else 0}")
        print(f"Max transactions/card:    {int(counts.max()) if not counts.empty else 0}")
        print(f"Avg transactions/card:    {counts.mean():.2f}" if not counts.empty else "Avg transactions/card:    0.00")
        print(f"Cards with 1 transaction:  {minimal_cards:,}")
        if minimal_cards == 0:
            print("Note: the source dataset contains no cards with only 1 transaction.")
        return len(rows)
    except Exception as error:
        connection.rollback()
        print(f"Database seeding failed: {error}")
        raise
    finally:
        connection.close()


def seed_card_history(card_id: str) -> int:
    """Insert a complete source history for one card when it is requested on demand."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    data = pd.read_csv(DATA_PATH)
    data["card_id"] = data["card_id"].astype(str)
    card_rows = data[data["card_id"] == str(card_id)].copy()
    if card_rows.empty:
        return 0

    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("Could not connect to PostgreSQL for on-demand card seeding.")
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(CREATE_TABLE_SQL)
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE card_id = %s", (str(card_id),))
                existing_count = int(cursor.fetchone()[0])
                if existing_count:
                    return existing_count
                rows = []
                for row in card_rows.to_dict(orient="records"):
                    rows.append(
                        (
                            str(row["card_id"]),
                            str(row["device_id"]),
                            float(row["Time"]),
                            float(row["Amount"]),
                            Json({column: float(row[column]) for column in V_COLUMNS}),
                            str(row["purchaser_email_domain"]),
                            str(row["recipient_email_domain"]),
                            int(row["Class"]),
                        )
                    )
                cursor.executemany(INSERT_SQL, rows)
                print(f"[seed_card_history] card_id={card_id!r} inserted={len(rows)}")
                return len(rows)
    finally:
        connection.close()


if __name__ == "__main__":
    seed_database()
