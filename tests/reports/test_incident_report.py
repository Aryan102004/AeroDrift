
from pathlib import Path

from reportlab.lib.utils import open_for_read

from aerodrift.reports.incident_report import generate_incident_report


def test_generates_pdf_incident_report(tmp_path):
    output = tmp_path / "incident.pdf"

    comparison = {
        "previous_snapshot_id": 1,
        "current_snapshot_id": 2,
        "has_changes": True,
        "added_nodes": ["db-prod-001"],
        "removed_nodes": [],
        "added_edges": [["internet", "subnet-private-001"]],
        "removed_edges": [],
        "changed_nodes": [],
        "changed_edges": [],
    }

    result = generate_incident_report(
        comparison,
        output_path=output,
        findings=["Synthetic database exposure detected"],
        remediation_actions=["Mock request recorded; no AWS change"],
        execution_mode="MOCK",
    )

    assert Path(result).exists()
    assert Path(result).stat().st_size > 0

    with open(result, "rb") as pdf_file:
        assert pdf_file.read(5) == b"%PDF-"


def test_generates_report_when_no_changes(tmp_path):
    output = tmp_path / "clean.pdf"

    comparison = {
        "previous_snapshot_id": 1,
        "current_snapshot_id": 2,
        "has_changes": False,
        "added_nodes": [],
        "removed_nodes": [],
        "added_edges": [],
        "removed_edges": [],
        "changed_nodes": [],
        "changed_edges": [],
    }

    result = generate_incident_report(comparison, output_path=output)

    assert Path(result).exists()
    assert Path(result).stat().st_size > 0
