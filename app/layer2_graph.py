"""Layer 2 graph rules for device and card relationships."""

from typing import Optional

from app.db_neo4j import get_neo4j_driver


DEVICE_CARD_LIMIT = 3


def record_transaction_link(device_id: str, card_id: str) -> bool:
    """Create a Device, Card, and USED_ON relationship in Neo4j."""
    driver = get_neo4j_driver()
    if driver is None:
        print("Graph link failed: Neo4j driver unavailable.")
        return False

    query = """
    MERGE (device:Device {device_id: $device_id})
    MERGE (card:Card {card_id: $card_id})
    MERGE (device)-[:USED_ON]->(card)
    """
    try:
        with driver.session() as session:
            session.run(query, device_id=device_id, card_id=card_id).consume()
        print(f"Recorded device {device_id} to card {card_id}.")
        return True
    except Exception as error:
        print(f"Graph link failed for device {device_id}, card {card_id}: {error}")
        return False
    finally:
        driver.close()


def get_device_card_count(device_id: str) -> Optional[int]:
    """Return distinct cards linked to a device, or None when the query fails."""
    driver = get_neo4j_driver()
    if driver is None:
        print("Graph count failed: Neo4j driver unavailable.")
        return None

    query = """
    MATCH (device:Device {device_id: $device_id})-[:USED_ON]->(card:Card)
    RETURN count(DISTINCT card) AS card_count
    """
    try:
        with driver.session() as session:
            record = session.run(query, device_id=device_id).single()
        count = int(record["card_count"]) if record is not None else 0
        print(f"Device {device_id} is linked to {count} distinct card(s).")
        return count
    except Exception as error:
        print(f"Graph count failed for device {device_id}: {error}")
        return None
    finally:
        driver.close()


def is_suspicious_device(device_id: str) -> bool:
    """Flag a device linked to more than three distinct cards."""
    card_count = get_device_card_count(device_id)
    return card_count is not None and card_count > DEVICE_CARD_LIMIT


if __name__ == "__main__":
    demo_device = "demo-device"
    for demo_card in ("demo-card-1", "demo-card-2", "demo-card-3", "demo-card-4"):
        record_transaction_link(demo_device, demo_card)
    count = get_device_card_count(demo_device)
    print(f"Demo result: count={count}, flagged={count is not None and count > 3}")
