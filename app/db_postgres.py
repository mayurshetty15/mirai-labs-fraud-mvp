"""PostgreSQL connection helpers."""

from typing import Optional

import psycopg2

from app import config


def get_postgres_connection() -> Optional[psycopg2.extensions.connection]:
    """Create and return a PostgreSQL connection, or None on failure."""
    try:
        connection = psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
        )
        print("PostgreSQL connection successful.")
        return connection
    except psycopg2.Error as error:
        print(f"PostgreSQL connection failed: {error}")
        return None


def test_connection() -> bool:
    """Run SELECT 1 to verify PostgreSQL connectivity."""
    connection = get_postgres_connection()
    if connection is None:
        return False

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        success = result == (1,)
        if success:
            print("PostgreSQL test query succeeded.")
        else:
            print(f"PostgreSQL test query returned an unexpected result: {result}")
        return success
    except psycopg2.Error as error:
        print(f"PostgreSQL test query failed: {error}")
        return False
    finally:
        connection.close()
