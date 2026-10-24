
import networkx as nx

from aerodrift.storage.snapshot_store import save_snapshot
from aerodrift.storage.comparator import compare_snapshots



def test_detects_added_and_removed_nodes_and_edges(tmp_path):
    db_path = tmp_path / "history.db"

    baseline = nx.DiGraph()
    baseline.add_node("vpc-1", resource_type="vpc")
    baseline.add_node("subnet-1", resource_type="subnet")
    baseline.add_edge("vpc-1", "subnet-1", relationship="contains")

    current = nx.DiGraph()
    current.add_node("vpc-1", resource_type="vpc")
    current.add_node("db-1", resource_type="database")
    current.add_edge("vpc-1", "db-1", relationship="network_path")

    previous_id = save_snapshot(baseline, "baseline", db_path)
    current_id = save_snapshot(current, "current", db_path)

    result = compare_snapshots(previous_id, current_id, db_path)

    assert result["added_nodes"] == ["db-1"]
    assert result["removed_nodes"] == ["subnet-1"]
    assert result["added_edges"] == [["vpc-1", "db-1"]]
    assert result["removed_edges"] == [["vpc-1", "subnet-1"]]
    assert result["has_changes"] is True



def test_detects_node_attribute_changes(tmp_path):
    db_path = tmp_path / "history.db"

    baseline = nx.DiGraph()
    baseline.add_node("subnet-1", subnet_type="private")

    current = nx.DiGraph()
    current.add_node("subnet-1", subnet_type="public")

    first_id = save_snapshot(baseline, "before", db_path)
    second_id = save_snapshot(current, "after", db_path)

    result = compare_snapshots(first_id, second_id, db_path)

    assert len(result["changed_nodes"]) == 1
    assert result["changed_nodes"][0]["id"] == "subnet-1"
    assert result["has_changes"] is True


def test_identical_snapshots_have_no_changes(tmp_path):
    db_path = tmp_path / "history.db"

    graph = nx.DiGraph()
    graph.add_node("vpc-1", resource_type="vpc")

    first_id = save_snapshot(graph, "first", db_path)
    second_id = save_snapshot(graph, "second", db_path)

    result = compare_snapshots(first_id, second_id, db_path)

    assert result["has_changes"] is False
    assert result["added_nodes"] == []
    assert result["removed_nodes"] == []
