"""Layer 1 rules for transaction velocity detection."""

from datetime import datetime, timezone
from typing import Union
from uuid import uuid4

from app.db_redis import get_redis_client


VELOCITY_WINDOW_SECONDS = 60
VELOCITY_LIMIT = 3
VELOCITY_KEY_PREFIX = "mirai:velocity:"


def _timestamp_seconds(transaction_time: Union[datetime, int, float]) -> float:
    """Convert a datetime or numeric timestamp to Unix seconds."""
    if isinstance(transaction_time, datetime):
        if transaction_time.tzinfo is None:
            transaction_time = transaction_time.replace(tzinfo=timezone.utc)
        return transaction_time.timestamp()
    return float(transaction_time)


def check_velocity(
    card_id: str, transaction_time: Union[datetime, int, float]
) -> tuple[bool, int]:
    """Return whether velocity is risky and the exact rolling-window count."""
    client = get_redis_client()
    if client is None:
        print("Velocity check failed: Redis client unavailable.")
        return False, 0

    key = f"{VELOCITY_KEY_PREFIX}{card_id}"
    current_time = _timestamp_seconds(transaction_time)
    event_id = f"{current_time}:{uuid4().hex}"

    try:
        pipeline = client.pipeline()
        pipeline.zremrangebyscore(key, 0, current_time - VELOCITY_WINDOW_SECONDS)
        pipeline.zadd(key, {event_id: current_time})
        pipeline.zcard(key)
        pipeline.expire(key, 24 * 60 * 60)
        _, _, transaction_count, _ = pipeline.execute()
        flagged = transaction_count > VELOCITY_LIMIT
        print(
            f"Velocity check for card {card_id}: "
            f"{transaction_count} transaction(s) in the last 60 seconds; "
            f"flagged={flagged}."
        )
        return flagged, int(transaction_count)
    except Exception as error:
        print(f"Velocity check failed for card {card_id}: {error}")
        return False, 0
    finally:
        client.close()


if __name__ == "__main__":
    for call_number in range(1, 6):
        result = check_velocity("demo-card", datetime.now(timezone.utc))
        print(f"Rapid call {call_number}: flagged={result[0]}, count={result[1]}")
