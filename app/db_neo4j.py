"""Neo4j connection helpers."""

from typing import Optional

from neo4j import Driver, GraphDatabase

from app import config


def get_neo4j_driver() -> Optional[Driver]:
    """Create and return a Neo4j driver, or None on failure."""
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD),
        )
        driver.verify_connectivity()
        print("Neo4j connection successful.")
        return driver
    except Exception as error:
        print(f"Neo4j connection failed: {error}")
        return None


def test_connection() -> bool:
    """Run a simple Cypher query and close the driver afterward."""
    driver = get_neo4j_driver()
    if driver is None:
        return False

    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS result").single()
        success = result is not None and result["result"] == 1
        if success:
            print("Neo4j test query succeeded.")
        else:
            print(f"Neo4j test query returned an unexpected result: {result}")
        return success
    except Exception as error:
        print(f"Neo4j test query failed: {error}")
        return False
    finally:
        driver.close()
