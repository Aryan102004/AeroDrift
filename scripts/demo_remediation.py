
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from aerodrift.remediation.generator import (
    IngressRuleFinding,
    generate_rollback_code,
)
from aerodrift.remediation.executor import execute_rollback


console = Console()


class MockRollbackClient:
    """Records rollback requests without modifying AWS."""

    def __init__(self):
        self.calls = []

    def revoke_security_group_ingress(self, **kwargs):
        self.calls.append(kwargs)
        return {"Return": True}


def main():
    # Demonstration input only; no live AWS rule is inspected.
    finding = IngressRuleFinding(
        group_id="sg-demo-001",
        protocol="tcp",
        from_port=8080,
        to_port=8080,
        source="0.0.0.0/0",
    )

    code = generate_rollback_code(finding)

    console.print(
        Panel(
            "[bold yellow]MOCK REMEDIATION PREVIEW[/bold yellow]\n"
            "No live AWS resources will be changed.",
            border_style="yellow",
        )
    )
    console.print("[cyan]Generated rollback code:[/cyan]")
    console.print(code)

    if not Confirm.ask(
        "Execute this approved request against the mock client?",
        default=False,
    ):
        console.print("[yellow]Execution cancelled.[/yellow]")
        return

    mock_client = MockRollbackClient()
    execute_rollback(code, mock_client)

    console.print(
        f"[green]Mock execution completed. "
        f"Recorded requests: {len(mock_client.calls)}[/green]"
    )
    console.print(
        "[dim]This records a simulated API request; it does not "
        "revoke a real security-group rule.[/dim]"
    )


if __name__ == "__main__":
    main()
