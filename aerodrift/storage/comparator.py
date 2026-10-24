
"""Compare two saved cloud topology snapshots."""

import networkx as nx

from aerodrift.storage.snapshot_store import load_snapshot


def compare_snapshots(
    previous_id: int,
    current_id: int,
    db_path="data/aerodrift.db",
) -> dict:
    """Return added and removed nodes and edges between snapshots."""
    previous = load_snapshot(previous_id, db_path)
    current = load_snapshot(current_id, db_path)

    previous_nodes = set(previous.nodes)
    current_nodes = set(current.nodes)
    previous_edges = set(previous.edges)
    current_edges = set(current.edges)

    added_nodes = sorted(current_nodes - previous_nodes)
    removed_nodes = sorted(previous_nodes - current_nodes)
    added_edges = sorted(current_edges - previous_edges)
    removed_edges = sorted(previous_edges - current_edges)

    # Detect attribute changes for resources present in both snapshots.
    changed_nodes = []
    for node_id in sorted(previous_nodes & current_nodes):
        before = dict(previous.nodes[node_id])
        after = dict(current.nodes[node_id])
        if before != after:
            changed_nodes.append({
                "id": node_id,
                "previous": before,
                "current": after,
            })

    changed_edges = []
    for source, target in sorted(previous_edges & current_edges):
        before = dict(previous.edges[source, target])
        after = dict(current.edges[source, target])
        if before != after:
            changed_edges.append({
                "source": source,
                "target": target,
                "previous": before,
                "current": after,
            })

    return {
        "previous_snapshot_id": previous_id,
        "current_snapshot_id": current_id,
        "added_nodes": added_nodes,
        "removed_nodes": removed_nodes,
        "added_edges": [list(edge) for edge in added_edges],
        "removed_edges": [list(edge) for edge in removed_edges],
        "changed_nodes": changed_nodes,
        "changed_edges": changed_edges,
        "has_changes": any((
            added_nodes, removed_nodes, added_edges, removed_edges,
            changed_nodes, changed_edges,
        )),
    }
