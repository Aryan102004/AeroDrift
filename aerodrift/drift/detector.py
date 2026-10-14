
from dataclasses import dataclass
import networkx as nx


INTERNET_NODE = "internet"


@dataclass
class DriftFinding:
    resource_id: str
    message: str
    previous_path_exists: bool
    current_path_exists: bool
    path: list[str] | None = None

    @property
    def is_new_exposure(self) -> bool:
        return (
            not self.previous_path_exists
            and self.current_path_exists
        )


def detect_database_drift(
    previous_graph: nx.DiGraph,
    current_graph: nx.DiGraph,
) -> list[DriftFinding]:
    """
    Find database nodes that have become reachable from the Internet.

    This function compares graph reachability between two snapshots.
    It does not independently validate AWS packet-level permissions.
    """
    findings = []

    database_ids = {
        node
        for node, attrs in current_graph.nodes(data=True)
        if attrs.get("resource_type") == "database"
    }

    for database_id in sorted(database_ids):
        previously_reachable = (
            INTERNET_NODE in previous_graph
            and database_id in previous_graph
            and nx.has_path(previous_graph, INTERNET_NODE, database_id)
        )

        currently_reachable = (
            INTERNET_NODE in current_graph
            and nx.has_path(current_graph, INTERNET_NODE, database_id)
        )

        if currently_reachable and not previously_reachable:
            path = nx.shortest_path(
                current_graph,
                INTERNET_NODE,
                database_id,
            )

            findings.append(
                DriftFinding(
                    resource_id=database_id,
                    message=(
                        "A new Internet-to-database graph path appeared."
                    ),
                    previous_path_exists=False,
                    current_path_exists=True,
                    path=path,
                )
            )

    return findings
