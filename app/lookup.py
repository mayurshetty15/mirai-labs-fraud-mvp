"""PostgreSQL transaction lookup and analyst decision persistence."""

from typing import Any

from app.db_postgres import get_postgres_connection


TRANSACTION_COLUMNS = """
transaction_id, card_id, device_id, time, amount, v_features,
purchaser_email_domain, recipient_email_domain, class_label,
gbt_score, decision, reviewed_by_human
"""


def _rows_as_dicts(cursor) -> list[dict[str, Any]]:
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_transaction_by_card_id(
    card_id: str, as_of: float | None = None
) -> dict[str, Any] | None:
    """Return the most recent transaction for a card."""
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable for transaction lookup.")
    try:
        with connection.cursor() as cursor:
            query = (
                f"SELECT {TRANSACTION_COLUMNS} FROM transactions "
                "WHERE card_id = %s"
            )
            parameters: list[Any] = [card_id]
            if as_of is not None:
                query += " AND time < %s"
                parameters.append(float(as_of))
            query += " ORDER BY time DESC, transaction_id DESC LIMIT 1"
            cursor.execute(query, parameters)
            rows = _rows_as_dicts(cursor)
        return rows[0] if rows else None
    finally:
        connection.close()


def get_card_history(
    card_id: str, limit: int = 10, as_of: float | None = None
) -> list[dict[str, Any]]:
    """Return the most recent transactions associated with a card."""
    print(f"[lookup.get_card_history] card_id={card_id!r} as_of={as_of!r} limit={limit}")
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable for card history lookup.")
    try:
        with connection.cursor() as cursor:
            query = (
                "SELECT transaction_id, time, amount, decision, class_label, "
                "purchaser_email_domain, recipient_email_domain "
                "FROM transactions WHERE card_id = %s"
            )
            parameters: list[Any] = [card_id]
            if as_of is not None:
                query += " AND time < %s"
                parameters.append(float(as_of))
            query += " ORDER BY time DESC, transaction_id DESC LIMIT %s"
            parameters.append(limit)
            cursor.execute(query, parameters)
            rows = _rows_as_dicts(cursor)
            print(
                f"[lookup.get_card_history] card_id={card_id!r} "
                f"as_of={as_of!r} returned={len(rows)}"
            )
            return rows
    finally:
        connection.close()


def get_flagged_queue(limit: int = 20) -> list[dict[str, Any]]:
    """Return scored transactions ordered by highest model risk first."""
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable for queue lookup.")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT transaction_id, card_id, device_id, amount, gbt_score, "
                "decision, time FROM transactions "
                "WHERE gbt_score IS NOT NULL ORDER BY gbt_score DESC, time DESC LIMIT %s",
                (limit,),
            )
            return _rows_as_dicts(cursor)
    finally:
        connection.close()


def get_unscored_transactions() -> list[dict[str, Any]]:
    """Return all transactions that still need pipeline scoring."""
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable for batch scoring.")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {TRANSACTION_COLUMNS} FROM transactions "
                "WHERE gbt_score IS NULL ORDER BY transaction_id"
            )
            return _rows_as_dicts(cursor)
    finally:
        connection.close()


def update_score(transaction_id: int, gbt_score: float, decision: str) -> None:
    """Persist automated score and decision without marking human review."""
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable while saving score.")
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE transactions SET gbt_score = %s, decision = %s "
                    "WHERE transaction_id = %s",
                    (float(gbt_score), decision, transaction_id),
                )
    finally:
        connection.close()


def update_scores(scores: list[tuple[int, float, str]]) -> None:
    """Persist a batch of automated scores in one PostgreSQL transaction."""
    if not scores:
        return
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable while saving scores.")
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    "UPDATE transactions SET gbt_score = %s, decision = %s "
                    "WHERE transaction_id = %s",
                    [(score, decision, transaction_id) for transaction_id, score, decision in scores],
                )
    finally:
        connection.close()


def update_decision(
    transaction_id: int,
    decision: str,
    reviewed_by_human: bool = True,
) -> None:
    """Persist an analyst's final decision."""
    if decision not in {"allow", "review", "block"}:
        raise ValueError("Decision must be allow, review, or block.")
    connection = get_postgres_connection()
    if connection is None:
        raise ConnectionError("PostgreSQL is unavailable while saving decision.")
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE transactions SET decision = %s, reviewed_by_human = %s "
                    "WHERE transaction_id = %s",
                    (decision, reviewed_by_human, transaction_id),
                )
    finally:
        connection.close()
