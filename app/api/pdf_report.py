from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

REPORT_DIR = Path(__file__).resolve().parents[2] / "reports"
REPORT_DIR.mkdir(exist_ok=True)


def generate_report_pdf(check_id: str, posting_text: str, risk_score: float,
                         verdict: str, red_flags: list[dict], explanation: str,
                         created_at: str) -> str:
    filepath = REPORT_DIR / f"report_{check_id}.pdf"
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Job Posting Authenticity Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {created_at}", styles["Normal"]))
    story.append(Paragraph(f"Check ID: {check_id}", styles["Normal"]))
    story.append(Spacer(1, 16))

    verdict_label = {"high_risk": "HIGH RISK", "medium_risk": "MEDIUM RISK", "low_risk": "LOW RISK"}[verdict]
    story.append(Paragraph(f"Verdict: {verdict_label}  ({risk_score:.0%} risk score)", styles["Heading1"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("AI Explanation", styles["Heading2"]))
    story.append(Paragraph(explanation, styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Red Flags Detected", styles["Heading2"]))
    if red_flags:
        data = [["Flag", "Evidence"]] + [[f["flag"], f["evidence"]] for f in red_flags]
        table = Table(data, colWidths=[150, 320])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("None detected.", styles["Normal"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Original Posting Text", styles["Heading2"]))
    story.append(Paragraph(posting_text[:2000], styles["Normal"]))

    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    doc.build(story)
    return str(filepath)