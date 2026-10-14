
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt

from aerodrift.drift.detector import DriftFinding


console = Console()


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
        internet_branch = root.add("[bold yellow]Internet (internet)[/bold yellow]")
        add_children(internet_branch, "internet")

    # Show resources not reachable from the Internet as well.
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
    """Render topology and drift findings in the terminal."""
    console.clear()

    console.print(
        Panel(
            "[bold cyan]AERODRIFT[/bold cyan]\n"
            "Agentic Cloud Topology & Remediation Graph",
            subtitle="Week 2 | Cloud Security Audit",
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


def run_dashboard(graph, findings: list[DriftFinding]) -> None:
    """Offer a simple interactive terminal menu."""
    while True:
        console.print("\n[bold cyan]AeroDrift Dashboard Menu[/bold cyan]")
        console.print("1. View cloud topology and drift findings")
        console.print("2. View drift findings only")
        console.print("3. Exit")

        choice = Prompt.ask(
            "Select an option",
            choices=["1", "2", "3"],
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

        else:
            console.print("[cyan]Exiting AeroDrift dashboard.[/cyan]")
            break
