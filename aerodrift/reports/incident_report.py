
"""Generate PDF incident reports for AeroDrift topology drift."""

from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_incident_report(
    comparison: dict,
    output_path="reports/aerodrift_incident_report.pdf",
    findings=None,
    remediation_actions=None,
    execution_mode="MOCK",
) -> str:
    """Create a PDF report and return its output path.

    Findings and remediation actions are descriptive records supplied by
    the caller. This function does not execute remediation.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    findings = findings or []
    remediation_actions = remediation_actions or []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=19,
        leading=24,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#12304A"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#087E8B"),
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SmallBody",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        wordWrap="CJK",
    ))

    story = [
        Paragraph("AeroDrift Incident Report", styles["ReportTitle"]),
        Paragraph(
            "Agentic Cloud Topology &amp; Remediation Graph",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            styles["SmallBody"],
        ),
        Paragraph(
            f"Execution mode: {execution_mode}",
            styles["SmallBody"],
        ),
        Paragraph(
            "This report describes recorded data only. A mock execution "
            "does not mean that an AWS resource was changed.",
            styles["SmallBody"],
        ),
        Paragraph("Snapshot Comparison", styles["SectionHeading"]),
    ]

    summary_rows = [
        ["Field", "Value"],
        ["Previous snapshot ID", str(comparison.get("previous_snapshot_id", "N/A"))],
        ["Current snapshot ID", str(comparison.get("current_snapshot_id", "N/A"))],
        ["Changes detected", "Yes" if comparison.get("has_changes") else "No"],
        ["Added nodes", str(len(comparison.get("added_nodes", [])))],
        ["Removed nodes", str(len(comparison.get("removed_nodes", [])))],
        ["Added edges", str(len(comparison.get("added_edges", [])))],
        ["Removed edges", str(len(comparison.get("removed_edges", [])))],
        ["Changed nodes", str(len(comparison.get("changed_nodes", [])))],
        ["Changed edges", str(len(comparison.get("changed_edges", [])))],
    ]

    summary_table = Table(summary_rows, colWidths=[55 * mm, 110 * mm], repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12304A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D5DF")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4F8FB")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([summary_table, Spacer(1, 3 * mm)])

    def add_list_section(title, key, label):
        story.append(Paragraph(title, styles["SectionHeading"]))
        items = comparison.get(key, [])
        if not items:
            story.append(Paragraph("None recorded.", styles["SmallBody"]))
            return

        rows = [["#", label]]
        for index, item in enumerate(items, 1):
            rows.append([
                str(index),
                Paragraph(
                    str(item).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                    styles["SmallBody"],
                ),
            ])

        table = Table(rows, colWidths=[12 * mm, 153 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEBF2")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D5DF")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)

    add_list_section("Added Resources", "added_nodes", "Resource ID")
    add_list_section("Removed Resources", "removed_nodes", "Resource ID")
    add_list_section("Added Relationships", "added_edges", "Source → target")
    add_list_section("Removed Relationships", "removed_edges", "Source → target")
    add_list_section("Changed Resource Attributes", "changed_nodes", "Details")
    add_list_section("Changed Relationship Attributes", "changed_edges", "Details")

    story.append(Paragraph("Drift Findings", styles["SectionHeading"]))
    if findings:
        for index, finding in enumerate(findings, 1):
            story.append(Paragraph(
                f"{index}. {str(finding)}".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                styles["SmallBody"],
            ))
            story.append(Spacer(1, 2 * mm))
    else:
        story.append(Paragraph("No findings supplied.", styles["SmallBody"]))

    story.append(Paragraph("Remediation Actions", styles["SectionHeading"]))
    if remediation_actions:
        for index, action in enumerate(remediation_actions, 1):
            story.append(Paragraph(
                f"{index}. {str(action)}".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                styles["SmallBody"],
            ))
            story.append(Spacer(1, 2 * mm))
    else:
        story.append(Paragraph("No remediation actions supplied.", styles["SmallBody"]))

    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        "AeroDrift prototype report · Verify findings before taking action.",
        styles["SmallBody"],
    ))

    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="AeroDrift Incident Report",
        author="AeroDrift",
    )
    document.build(story)
    return str(output.resolve())
