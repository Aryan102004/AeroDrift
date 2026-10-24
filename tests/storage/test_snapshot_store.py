
import networkx as nx
import pytest

from aerodrift.storage.snapshot_store import (
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture
def graph():
    result = nx.DiGraph()
    result.add_node(
        "vpc-001",
        resource_type="vpc",
        name="production-vpc",
    )
    result.add_node(
        "subnet-private-001",
        resource_type="subnet",
        subnet_type="private",
    )
    result.add_edge(
        "vpc-001",
        "subnet-private-001",
        relationship="contains",
    )
    return result


def test_save_and_restore_snapshot(tmp_path, graph):
    db_path = tmp_path / "test.db"

    snapshot_id = save_snapshot(graph, "baseline", db_path)
    restored = load_snapshot(snapshot_id, db_path)

    assert set(restored.nodes) == set(graph.nodes)
    assert set(restored.edges) == set(graph.edges)
    assert restored.nodes["vpc-001"]["name"] == "production-vpc"
    assert restored.edges["vpc-001", "subnet-private-001"][
        "relationship"
    ] == "contains"


def test_snapshot_metadata_is_listed(tmp_path, graph):
    db_path = tmp_path / "test.db"

    snapshot_id = save_snapshot(graph, "baseline", db_path)
    snapshots = list_snapshots(db_path)

    assert len(snapshots) == 1
    assert snapshots[0]["id"] == snapshot_id
    assert snapshots[0]["label"] == "baseline"
    assert snapshots[0]["timestamp"]


def test_snapshots_have_distinct_ids(tmp_path, graph):
    db_path = tmp_path / "test.db"

    first = save_snapshot(graph, "baseline", db_path)
    second = save_snapshot(graph, "current", db_path)

    assert first != second
    assert len(list_snapshots(db_path)) == 2


def test_empty_label_is_rejected(tmp_path, graph):
    with pytest.raises(ValueError, match="label"):
        save_snapshot(graph, "  ", tmp_path / "test.db")


def test_unknown_snapshot_id_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        load_snapshot(999, tmp_path / "test.db")
