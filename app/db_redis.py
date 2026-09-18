"""Redis Cloud connection helpers."""

from typing import Optional

import redis

from app import config


def get_redis_client() -> Optional[redis.Redis]:
    """Create and return a Redis Cloud client, or None on failure."""
    try:
        client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            username=config.REDIS_USERNAME,
            password=config.REDIS_PASSWORD,
            decode_responses=True,
            ssl=False,
        )
        client.ping()
        print("Redis connection successful.")
        return client
    except redis.RedisError as error:
        print(f"Redis connection failed: {error}")
        return None


def test_connection() -> bool:
    """Verify Redis read/write access with a temporary test key."""
    client = get_redis_client()
    if client is None:
        return False

    try:
        test_key = "mirai_test_key"
        expected_value = "mirai_test_value"
        client.set(test_key, expected_value)
        actual_value = client.get(test_key)
        success = actual_value == expected_value
        if success:
            print("Redis SET/GET test succeeded.")
        else:
            print(f"Redis test returned an unexpected value: {actual_value}")
        return success
    except redis.RedisError as error:
        print(f"Redis SET/GET test failed: {error}")
        return False
    finally:
        try:
            client.delete("mirai_test_key")
            client.close()
        except redis.RedisError as error:
            print(f"Redis cleanup failed: {error}")
