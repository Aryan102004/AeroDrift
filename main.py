
import asyncio
import copy

from rich.console import Console

from aerodrift.collectors.aws_collector import AWSCollector
from aerodrift.collectors.mock_aws_client import MockAWSClient
from aerodrift.topology.graph import CloudTopology
from aerodrift.drift.detector import detect_database_drift
from aerodrift.dashboard.cli import run_dashboard


console = Console()


async def main():
    console.print("[bold cyan]AERODRIFT — WEEK 2[/bold cyan]")
    console.print("Cloud Drift Detection and CLI Dashboard\n")

    # 1. Collect the existing Week 1 mock infrastructure.
    client = MockAWSClient()
    collector = AWSCollector(client)
    state = await collector.collect_all()

    console.print("[green]Cloud-state collection completed.[/green]")

    # 2. Build the baseline topology.
    baseline_topology = CloudTopology()
    baseline_graph = baseline_topology.build(state)

    # 3. Simulate a private database for this Week 2 demonstration.
    # This database is synthetic; it is not collected from AWS.
    previous_graph = copy.deepcopy(baseline_graph)
    current_graph = copy.deepcopy(baseline_graph)

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

    # 4. Simulate a new Internet route to the private subnet.
    # This represents a hypothetical topology drift event.
    current_graph.add_edge(
        "internet",
        private_subnet_id,
        relationship="simulated_drift",
    )

    # 5. Detect newly appearing Internet-to-database paths.
    findings = detect_database_drift(
        previous_graph,
        current_graph,
    )

    console.print(
        f"[cyan]New exposure findings: {len(findings)}[/cyan]\n"
    )

    # 6. Launch the interactive Rich dashboard.
    run_dashboard(current_graph, findings)


if __name__ == "__main__":
    asyncio.run(main())
