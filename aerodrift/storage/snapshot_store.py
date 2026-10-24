
"""Persist and restore historical AeroDrift topology snapshots."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx


DEFAULT_DB_PATH = Path("data") / "aerodrift.db"


def _serialize_graph(graph: nx.DiGraph) -> str:
    """Serialize graph nodes, edges, and attributes to JSON."""
    payload = {
        "directed": graph.is_directed(),
        "nodes": [
            {"id": node_id, "attributes": dict(attributes)}
            for node_id, attributes in graph.nodes(data=True)
        ],
        "edges": [
            {
                "source": source,
                "target": target,
                "attributes": dict(attributes),
            }
            for source, target, attributes in graph.edges(data=True)
        ],
    }
    return json.dumps(payload, sort_keys=True)


def _deserialize_graph(graph_json: str) -> nx.DiGraph:
    """Restore a graph from a stored JSON snapshot."""
    payload = json.loads(graph_json)

    if not payload.get("directed", False):
        raise ValueError("Snapshot must contain a directed graph.")

    graph = nx.DiGraph()

    for node in payload["nodes"]:
        graph.add_node(node["id"], **node["attributes"])

    for edge in payload["edges"]:
        graph.add_edge(
            edge["source"],
            edge["target"],
            **edge["attributes"],
        )

    return graph


def initialize_database(db_path=DEFAULT_DB_PATH) -> None:
    """Create the snapshot table if it does not exist."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS topology_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                graph_json TEXT NOT NULL
            )
            """
        )


def save_snapshot(
    graph: nx.DiGraph,
    label: str,
    db_path=DEFAULT_DB_PATH,
) -> int:
    """Save a graph snapshot and return its unique ID."""
    if not label or not label.strip():
        raise ValueError("Snapshot label cannot be empty.")

    if not graph.is_directed():
        raise ValueError("Only directed graphs are supported.")

    graph_json = _serialize_graph(graph)
    timestamp = datetime.now(timezone.utc).isoformat()

    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO topology_snapshots (label, timestamp, graph_json)
            VALUES (?, ?, ?)
            """,
            (label.strip(), timestamp, graph_json),
        )
        return cursor.lastrowid


def list_snapshots(db_path=DEFAULT_DB_PATH) -> list[dict]:
    """Return saved snapshot metadata in chronological order."""
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, label, timestamp
            FROM topology_snapshots
            ORDER BY timestamp ASC, id ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def load_snapshot(
    snapshot_id: int,
    db_path=DEFAULT_DB_PATH,
) -> nx.DiGraph:
    """Load a graph by its snapshot ID."""
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT graph_json
            FROM topology_snapshots
            WHERE id = ?
            """,
            (snapshot_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"Snapshot ID {snapshot_id} was not found.")

    return _deserialize_graph(row[0])
