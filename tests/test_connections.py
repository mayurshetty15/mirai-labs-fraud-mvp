"""Run connectivity checks for all MirAI database services."""

import sys
from pathlib import Path

# Allow this file to be run directly with: python tests/test_connections.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db_neo4j import test_connection as test_neo4j_connection
from app.db_postgres import test_connection as test_postgres_connection
from app.db_redis import test_connection as test_redis_connection


def main() -> None:
    """Run each check and print a compact summary table."""
    results = (
        ("PostgreSQL", test_postgres_connection()),
        ("Redis", test_redis_connection()),
        ("Neo4j", test_neo4j_connection()),
    )

    print("\nDatabase Connection Summary")
    print("---------------------------")
    print(f"{'Database':<15} Status")
    print(f"{'PostgreSQL':<15} {'SUCCESS' if results[0][1] else 'FAILED'}")
    print(f"{'Redis':<15} {'SUCCESS' if results[1][1] else 'FAILED'}")
    print(f"{'Neo4j':<15} {'SUCCESS' if results[2][1] else 'FAILED'}")


if __name__ == "__main__":
    main()
