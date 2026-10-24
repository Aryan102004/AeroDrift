
import asyncio
import copy

from rich.console import Console

from aerodrift.collectors.aws_collector import AWSCollector
from aerodrift.collectors.mock_aws_client import MockAWSClient
from aerodrift.topology.graph import CloudTopology
from aerodrift.drift.detector import detect_database_drift
from aerodrift.dashboard.cli import run_dashboard
from aerodrift.storage.snapshot_store import save_snapshot
from aerodrift.storage.comparator import compare_snapshots


console = Console()
DB_PATH = "data/aerodrift.db"


async def main():
    console.print("[bold cyan]AERODRIFT — WEEK 4[/bold cyan]")
    console.print("Historical State Persistence and Incident Reporting\n")

    # 1. Collect the existing Week 1 mock infrastructure.
    client = MockAWSClient()
    collector = AWSCollector(client)
    state = await collector.collect_all()

    console.print("[green]Mock cloud-state collection completed.[/green]")

    # 2. Build the baseline topology.
    baseline_topology = CloudTopology()
    baseline_graph = baseline_topology.build(state)

    previous_graph = copy.deepcopy(baseline_graph)
    current_graph = copy.deepcopy(baseline_graph)

    # 3. Preserve the existing synthetic Week 2 database example.
    database_id = "db-prod-001"
    private_subnet_id = "subnet-private-001"

    for graph in (previous_graph, current_graph):
        graph.add_node(
            database_id,
            resource_type="database",
            name="production-database",
            private_ip="10.0.2.20",
        )
        graph.add_edge(
            private_subnet_id,
            database_id,
            relationship="network_path",
        )

    # 4. Simulate a new Internet route in the current graph only.
    current_graph.add_edge(
        "internet",
        private_subnet_id,
        relationship="simulated_drift",
    )

    # 5. Detect newly appearing Internet-to-database paths.
    findings = detect_database_drift(previous_graph, current_graph)

    console.print(
        f"[cyan]New exposure findings: {len(findings)}[/cyan]"
    )

    # 6. Persist both graphs as timestamped SQLite snapshots.
    previous_id = save_snapshot(
        previous_graph,
        "baseline",
        DB_PATH,
    )
    current_id = save_snapshot(
        current_graph,
        "current-simulated-state",
        DB_PATH,
    )

    console.print(
        f"[green]Baseline snapshot saved: {previous_id}[/green]"
    )
    console.print(
        f"[green]Current snapshot saved: {current_id}[/green]"
    )

    # 7. Compare the newly saved snapshots.
    comparison = compare_snapshots(
        previous_id,
        current_id,
        DB_PATH,
    )

    console.print(
        "[yellow]Synthetic drift comparison completed.[/yellow]"
    )

    # 8. Launch the interactive Week 4 dashboard.
    run_dashboard(
        current_graph,
        findings,
        db_path=DB_PATH,
        comparison=comparison,
    )


if __name__ == "__main__":
    asyncio.run(main())
