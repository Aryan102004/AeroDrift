
import networkx as nx

from aerodrift.drift.detector import detect_database_drift


def make_graph(database_reachable: bool) -> nx.DiGraph:
    graph = nx.DiGraph()

    graph.add_node("internet", resource_type="external")
    graph.add_node("subnet-private", resource_type="subnet")
    graph.add_node("db-prod-001", resource_type="database")

    if database_reachable:
        graph.add_edge("internet", "subnet-private")
        graph.add_edge("subnet-private", "db-prod-001")

    return graph


def test_new_database_exposure_is_detected():
    previous = make_graph(database_reachable=False)
    current = make_graph(database_reachable=True)

    findings = detect_database_drift(previous, current)

    assert len(findings) == 1
    assert findings[0].resource_id == "db-prod-001"
    assert findings[0].is_new_exposure is True
    assert findings[0].path == [
        "internet",
        "subnet-private",
        "db-prod-001",
    ]


def test_database_without_internet_path_is_safe():
    previous = make_graph(database_reachable=False)
    current = make_graph(database_reachable=False)

    findings = detect_database_drift(previous, current)

    assert findings == []


def test_existing_exposure_does_not_trigger_new_drift():
    previous = make_graph(database_reachable=True)
    current = make_graph(database_reachable=True)

    findings = detect_database_drift(previous, current)

    assert findings == []
