"""Generate PDF report from analysis JSON."""

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf(report: dict[str, Any]) -> bytes:
    """Build PDF bytes from analysis result."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=inch, leftMargin=inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor("#1a1a2e"),
    )
    body = styles["Normal"]
    story = []

    story.append(Paragraph("Global AI Governance Copilot — Analysis Report", title_style))
    story.append(Spacer(1, 0.2 * inch))

    cov = report.get("coverage", {})
    summ = cov.get("summary", {})
    story.append(Paragraph(
        f"<b>Coverage:</b> {summ.get('covered', 0)} / {summ.get('total', 0)} sub-areas addressed "
        f"({summ.get('fraction', 0)*100:.1f}%).",
        body,
    ))
    story.append(Spacer(1, 0.15 * inch))

    conf = report.get("conflicts", {})
    story.append(Paragraph(f"<b>Conflict signals:</b> {conf.get('count', 0)}", body))
    story.append(Spacer(1, 0.15 * inch))

    rec = report.get("recommendations", {})
    for tier in ("minimal", "moderate", "strict"):
        block = rec.get(tier, {})
        story.append(Paragraph(f"<b>{block.get('title', tier)}</b>", body))
        story.append(Paragraph(block.get("summary", ""), body))
        story.append(Paragraph(f"<i>{block.get('sample_language', '')}</i>", body))
        story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return buf.getvalue()
