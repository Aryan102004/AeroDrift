
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from aerodrift.drift.detector import DriftFinding
from aerodrift.remediation.generator import (
    IngressRuleFinding,
    generate_rollback_code,
)
from aerodrift.remediation.executor import execute_rollback
from pathlib import Path

from aerodrift.storage.snapshot_store import (
    list_snapshots,
    save_snapshot,
)
from aerodrift.storage.comparator import compare_snapshots
from aerodrift.reports.incident_report import generate_incident_report


console = Console()


class MockRollbackClient:
    """Record remediation requests without modifying AWS."""

    def __init__(self):
        self.calls = []

    def revoke_security_group_ingress(self, **kwargs):
        self.calls.append(kwargs)
        return {"Return": True}


def build_topology_tree(graph) -> Tree:
    """Build a readable tree from the directed cloud graph."""
    root = Tree("[bold cyan]AeroDrift Cloud Topology[/bold cyan]")
    visited = set()

    def add_children(parent, node):
        for child in sorted(graph.successors(node)):
            if child in visited:
                continue

            visited.add(child)
            attrs = graph.nodes[child]
            resource_type = attrs.get("resource_type", "resource")
            name = attrs.get("name", child)

            branch = parent.add(
                f"[bold]{name}[/bold] "
                f"[dim]({resource_type}: {child})[/dim]"
            )
            add_children(branch, child)

    if "internet" in graph:
        visited.add("internet")
        internet_branch = root.add(
            "[bold yellow]Internet (internet)[/bold yellow]"
        )
        add_children(internet_branch, "internet")

    remaining = sorted(set(graph.nodes) - visited)

    if remaining:
        isolated = root.add("[bold]Other cloud resources[/bold]")
        for node in remaining:
            attrs = graph.nodes[node]
            resource_type = attrs.get("resource_type", "resource")
            name = attrs.get("name", node)
            isolated.add(
                f"{name} [dim]({resource_type}: {node})[/dim]"
            )

    return root


def render_dashboard(graph, findings: list[DriftFinding]) -> None:
    """Render topology and database drift findings."""
    console.clear()

    console.print(
        Panel(
            "[bold cyan]AERODRIFT[/bold cyan]\n"
            "Agentic Cloud Topology & Remediation Graph",
            subtitle="Week 3 | Cloud Security Audit",
            border_style="cyan",
        )
    )

    summary = Table(title="Infrastructure Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", justify="right")
    summary.add_row("Graph nodes", str(graph.number_of_nodes()))
    summary.add_row("Graph edges", str(graph.number_of_edges()))
    summary.add_row("New exposure findings", str(len(findings)))
    console.print(summary)

    console.print()
    console.print(build_topology_tree(graph))
    console.print()

    if findings:
        alerts = Table(
            title="New Internet-to-Database Exposure",
            show_lines=True,
        )
        alerts.add_column("Severity", style="bold red")
        alerts.add_column("Database")
        alerts.add_column("Finding")
        alerts.add_column("Path")

        for finding in findings:
            alerts.add_row(
                "HIGH",
                finding.resource_id,
                finding.message,
                " -> ".join(finding.path or []),
            )

        console.print(alerts)
    else:
        console.print(
            Panel(
                "[bold green]No newly appearing "
                "Internet-to-database paths detected.[/bold green]",
                title="Drift Status",
                border_style="green",
            )
        )


def run_mock_remediation() -> None:
    """
    Demonstrate generated remediation against a mock client only.

    This example rule is synthetic and is not derived from
    the database graph finding or live AWS configuration.
    """
    finding = IngressRuleFinding(
        group_id="sg-demo-001",
        protocol="tcp",
        from_port=8080,
        to_port=8080,
        source="0.0.0.0/0",
    )

    try:
        code = generate_rollback_code(finding)
    except ValueError as exc:
        console.print(f"[bold red]Generation rejected:[/bold red] {exc}")
        return

    console.print(
        Panel(
            "[bold yellow]MOCK REMEDIATION PREVIEW[/bold yellow]\n"
            "Synthetic example only. No live AWS rule is inspected "
            "or modified.",
            title="Remediation",
            border_style="yellow",
        )
    )
    console.print(
        Syntax(code, "python", theme="monokai", line_numbers=True)
    )

    if not Confirm.ask(
        "Execute this request against the mock client?",
        default=False,
    ):
        console.print("[yellow]Execution cancelled.[/yellow]")
        return

    mock_client = MockRollbackClient()

    try:
        execute_rollback(code, mock_client)
    except Exception as exc:
        console.print(
            f"[bold red]Mock execution failed:[/bold red] {exc}"
        )
        return

    if len(mock_client.calls) != 1:
        console.print(
            "[bold red]Unexpected mock request count.[/bold red]"
        )
        return

    console.print(
        "[bold green]Mock execution completed. "
        "Recorded requests: 1[/bold green]"
    )
    console.print(
        "[dim]No real AWS security-group rule was revoked.[/dim]"
    )

    audit = Table(title="Mock Remediation Audit")
    audit.add_column("Field", style="cyan")
    audit.add_column("Value")
    audit.add_row("Security group", finding.group_id)
    audit.add_row("Protocol", finding.protocol.upper())
    audit.add_row(
        "Port range",
        f"{finding.from_port}-{finding.to_port}",
    )
    audit.add_row("Source CIDR", finding.source)
    audit.add_row("Execution mode", "Mock only")
    audit.add_row("Recorded requests", str(len(mock_client.calls)))
    console.print(audit)


def save_topology_snapshot(graph, db_path="data/aerodrift.db"):
    """Save the current graph as a named historical snapshot."""
    label = Prompt.ask("Snapshot label", default="manual-snapshot")

    try:
        snapshot_id = save_snapshot(graph, label, db_path)
        console.print(
            f"[bold green]Snapshot saved. ID: {snapshot_id}[/bold green]"
        )
    except (ValueError, OSError) as exc:
        console.print(f"[bold red]Could not save snapshot:[/bold red] {exc}")


def show_saved_snapshots(db_path="data/aerodrift.db"):
    """Display all saved snapshot IDs and timestamps."""
    snapshots = list_snapshots(db_path)

    if not snapshots:
        console.print("[yellow]No snapshots saved yet.[/yellow]")
        return

    table = Table(title="Historical Topology Snapshots")
    table.add_column("ID", style="cyan")
    table.add_column("Label")
    table.add_column("Timestamp")

    for snapshot in snapshots:
        table.add_row(
            str(snapshot["id"]),
            snapshot["label"],
            snapshot["timestamp"],
        )

    console.print(table)


def choose_snapshot_id(snapshots, message):
    """Prompt for a snapshot ID from the saved snapshots."""
    valid_ids = [str(item["id"]) for item in snapshots]

    selected = Prompt.ask(
        message,
        choices=valid_ids,
    )
    return int(selected)


def compare_saved_snapshots(db_path="data/aerodrift.db"):
    """Compare two selected historical snapshots."""
    snapshots = list_snapshots(db_path)

    if len(snapshots) < 2:
        console.print(
            "[yellow]Save at least two snapshots before comparing.[/yellow]"
        )
        return None

    show_saved_snapshots(db_path)

    previous_id = choose_snapshot_id(
        snapshots, "Select previous snapshot ID"
    )
    current_id = choose_snapshot_id(
        snapshots, "Select current snapshot ID"
    )

    if previous_id == current_id:
        console.print(
            "[yellow]Choose two different snapshot IDs.[/yellow]"
        )
        return None

    try:
        result = compare_snapshots(previous_id, current_id, db_path)
    except (ValueError, OSError) as exc:
        console.print(f"[bold red]Comparison failed:[/bold red] {exc}")
        return None

    table = Table(title="Historical Snapshot Comparison")
    table.add_column("Change", style="cyan")
    table.add_column("Count", justify="right")

    for label, key in (
        ("Added resources", "added_nodes"),
        ("Removed resources", "removed_nodes"),
        ("Added relationships", "added_edges"),
        ("Removed relationships", "removed_edges"),
        ("Changed resource attributes", "changed_nodes"),
        ("Changed relationship attributes", "changed_edges"),
    ):
        table.add_row(label, str(len(result[key])))

    console.print(table)

    for label, key in (
        ("Added resources", "added_nodes"),
        ("Removed resources", "removed_nodes"),
        ("Added relationships", "added_edges"),
        ("Removed relationships", "removed_edges"),
        ("Changed resource attributes", "changed_nodes"),
        ("Changed relationship attributes", "changed_edges"),
    ):
        if result[key]:
            console.print(f"\n[bold]{label}[/bold]")
            for item in result[key]:
                console.print(f"  • {item}")

    if result["has_changes"]:
        console.print("[bold yellow]Topology changes detected.[/bold yellow]")
    else:
        console.print("[bold green]No topology changes detected.[/bold green]")

    return result


def create_pdf_incident_report(
    comparison,
    findings,
    db_path="data/aerodrift.db",
):
    """Generate a PDF report for a selected snapshot comparison."""
    if comparison is None:
        console.print(
            "[yellow]Run a successful snapshot comparison first.[/yellow]"
        )
        return

    output_path = (
        Path("reports")
        / (
            "aerodrift_incident_"
            f"{comparison['previous_snapshot_id']}_"
            f"{comparison['current_snapshot_id']}.pdf"
        )
    )

    finding_details = [
        (
            f"Severity: HIGH | Resource: {finding.resource_id} | "
            f"{finding.message} | Path: "
            f"{' -> '.join(finding.path or [])} | "
            "Source: current synthetic drift demonstration"
        )
        for finding in findings
    ]

    try:
        report_path = generate_incident_report(
            comparison,
            output_path=output_path,
            findings=finding_details,
            remediation_actions=[
                "No remediation execution was performed by report generation.",
                "Week 3 remediation remains mock-only and is separate from "
                "the synthetic database exposure finding.",
            ],
            execution_mode="MOCK / SYNTHETIC DEMO",
        )
    except (ValueError, OSError) as exc:
        console.print(f"[bold red]PDF generation failed:[/bold red] {exc}")
        return

    console.print(
        Panel(
            f"[bold green]Incident report generated[/bold green]\n{report_path}",
            title="PDF Report",
            border_style="green",
        )
    )



def run_dashboard(
    graph,
    findings: list[DriftFinding],
    db_path="data/aerodrift.db",
    comparison=None,
) -> None:
    """Offer topology, remediation, persistence, and report options."""
    while True:
        console.print("\n[bold cyan]AeroDrift Dashboard Menu[/bold cyan]")
        console.print("1. View cloud topology and drift findings")
        console.print("2. View drift findings only")
        console.print("3. Preview and run mock remediation")
        console.print("4. Save current topology snapshot")
        console.print("5. List historical snapshots")
        console.print("6. Compare two saved snapshots")
        console.print("7. Generate PDF incident report")
        console.print("8. Exit")

        choice = Prompt.ask(
            "Select an option",
            choices=["1", "2", "3", "4", "5", "6", "7", "8"],
            default="1",
        )

        if choice == "1":
            render_dashboard(graph, findings)

        elif choice == "2":
            if not findings:
                console.print("[green]No new exposure findings.[/green]")
            else:
                for finding in findings:
                    console.print(
                        f"[bold red]HIGH[/bold red] "
                        f"{finding.resource_id}: {finding.message}"
                    )
                    if finding.path:
                        console.print(" -> ".join(finding.path))

        elif choice == "3":
            run_mock_remediation()

        elif choice == "4":
            save_topology_snapshot(graph, db_path)

        elif choice == "5":
            show_saved_snapshots(db_path)

        elif choice == "6":
            comparison = compare_saved_snapshots(db_path)

        elif choice == "7":
            create_pdf_incident_report(
                comparison,
                findings,
                db_path,
            )

        else:
            console.print("[cyan]Exiting AeroDrift dashboard.[/cyan]")
            break

