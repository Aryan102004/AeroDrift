
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


def run_dashboard(graph, findings: list[DriftFinding]) -> None:
    """Offer topology, findings, and mock remediation options."""
    while True:
        console.print("\n[bold cyan]AeroDrift Dashboard Menu[/bold cyan]")
        console.print("1. View cloud topology and drift findings")
        console.print("2. View drift findings only")
        console.print("3. Preview and run mock remediation")
        console.print("4. Exit")

        choice = Prompt.ask(
            "Select an option",
            choices=["1", "2", "3", "4"],
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

        else:
            console.print("[cyan]Exiting AeroDrift dashboard.[/cyan]")
            break
