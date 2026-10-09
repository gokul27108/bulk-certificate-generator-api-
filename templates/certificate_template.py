"""Professional certificate PDF template using ReportLab.

This module defines the SINGLE predefined certificate template.
No template editor or multiple designs are supported - by design.

The certificate layout:
  - Decorative border
  - Organization name at top
  - Certificate title (large, centered)
  - Recipient name (prominent, large font)
  - Event/course information
  - Issue date
  - Professional typography with good spacing
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from io import BytesIO
import os


# ─── Color Palette ────────────────────────────────────────────────────────────
COLOR_DEEP_NAVY = colors.HexColor("#1A237E")    # Deep navy for borders and headings
COLOR_GOLD = colors.HexColor("#C9A84C")          # Gold for decorative elements
COLOR_DARK_GOLD = colors.HexColor("#8B6914")     # Darker gold for accents
COLOR_CHARCOAL = colors.HexColor("#2C3E50")      # Dark grey for body text
COLOR_LIGHT_GREY = colors.HexColor("#F8F9FA")    # Light background
COLOR_WHITE = colors.white


# ─── Paragraph Styles ─────────────────────────────────────────────────────────

def get_styles() -> dict:
    """Return a dictionary of named paragraph styles for the certificate."""
    return {
        "org_name": ParagraphStyle(
            name="OrgName",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=COLOR_DEEP_NAVY,
            alignment=TA_CENTER,
            spaceAfter=4,
            letterSpacing=2,
        ),
        "presents": ParagraphStyle(
            name="Presents",
            fontName="Helvetica",
            fontSize=11,
            textColor=COLOR_CHARCOAL,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "cert_title": ParagraphStyle(
            name="CertTitle",
            fontName="Helvetica-Bold",
            fontSize=32,
            textColor=COLOR_DEEP_NAVY,
            alignment=TA_CENTER,
            spaceAfter=8,
            leading=38,
        ),
        "awarded_to": ParagraphStyle(
            name="AwardedTo",
            fontName="Helvetica",
            fontSize=12,
            textColor=COLOR_CHARCOAL,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "recipient_name": ParagraphStyle(
            name="RecipientName",
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=COLOR_DEEP_NAVY,
            alignment=TA_CENTER,
            spaceAfter=8,
            leading=34,
        ),
        "for_completing": ParagraphStyle(
            name="ForCompleting",
            fontName="Helvetica",
            fontSize=12,
            textColor=COLOR_CHARCOAL,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "event_name": ParagraphStyle(
            name="EventName",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=COLOR_CHARCOAL,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "issue_date": ParagraphStyle(
            name="IssueDate",
            fontName="Helvetica",
            fontSize=11,
            textColor=COLOR_CHARCOAL,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
    }


def draw_certificate_border(canvas_obj, doc):
    """Draw the decorative border and background on the certificate page.

    This is called for each page by ReportLab as an onPage callback.

    Args:
        canvas_obj: ReportLab canvas object.
        doc: Document template.
    """
    canvas_obj.saveState()

    page_width, page_height = landscape(A4)

    # ── Light background fill ─────────────────────────────────────────────────
    canvas_obj.setFillColor(COLOR_LIGHT_GREY)
    canvas_obj.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # ── Outer thick border ────────────────────────────────────────────────────
    margin = 0.4 * inch
    canvas_obj.setStrokeColor(COLOR_DEEP_NAVY)
    canvas_obj.setLineWidth(4)
    canvas_obj.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin, fill=0, stroke=1)

    # ── Inner gold border ─────────────────────────────────────────────────────
    inner_margin = 0.55 * inch
    canvas_obj.setStrokeColor(COLOR_GOLD)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.rect(inner_margin, inner_margin, page_width - 2 * inner_margin, page_height - 2 * inner_margin, fill=0, stroke=1)

    # ── Corner ornaments (gold squares) ────────────────────────────────────────
    ornament_size = 0.12 * inch
    corners = [
        (margin - ornament_size / 2, margin - ornament_size / 2),
        (page_width - margin - ornament_size / 2, margin - ornament_size / 2),
        (margin - ornament_size / 2, page_height - margin - ornament_size / 2),
        (page_width - margin - ornament_size / 2, page_height - margin - ornament_size / 2),
    ]
    canvas_obj.setFillColor(COLOR_GOLD)
    for cx, cy in corners:
        canvas_obj.rect(cx, cy, ornament_size, ornament_size, fill=1, stroke=0)

    # ── Top gold decorative bar ───────────────────────────────────────────────
    bar_y = page_height - 1.2 * inch
    canvas_obj.setFillColor(COLOR_GOLD)
    canvas_obj.setLineWidth(0)
    canvas_obj.rect(inner_margin + 0.1 * inch, bar_y, page_width - 2 * inner_margin - 0.2 * inch, 3, fill=1, stroke=0)

    # ── Bottom gold decorative bar ────────────────────────────────────────────
    bar_bottom_y = inner_margin + 0.5 * inch
    canvas_obj.rect(inner_margin + 0.1 * inch, bar_bottom_y, page_width - 2 * inner_margin - 0.2 * inch, 3, fill=1, stroke=0)

    canvas_obj.restoreState()


def generate_certificate_pdf(
    recipient_name: str,
    certificate_title: str,
    event_name: str,
    organization_name: str,
    issue_date: str,
    output_path: str
) -> str:
    """Generate a professional certificate PDF and save it to disk.

    This is the single predefined certificate template.
    All certificates use this same layout.

    Args:
        recipient_name: Full name of the certificate recipient.
        certificate_title: Title of the certificate (e.g., 'Certificate of Completion').
        event_name: Name of the event or course.
        organization_name: Organization issuing the certificate.
        issue_date: Issue date string (formatted for display).
        output_path: Full filesystem path where the PDF will be saved.

    Returns:
        The output_path where the PDF was saved.

    Raises:
        Exception: If PDF generation fails for any reason.
    """
    page_width, page_height = landscape(A4)

    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.2 * inch,
        rightMargin=1.2 * inch,
        topMargin=1.4 * inch,
        bottomMargin=1.2 * inch,
    )

    styles = get_styles()
    story = []

    # ── Organization Name ─────────────────────────────────────────────────────
    story.append(Paragraph(organization_name.upper(), styles["org_name"]))
    story.append(Paragraph("PROUDLY PRESENTS", styles["presents"]))
    story.append(Spacer(1, 0.15 * inch))

    # ── Gold divider line ─────────────────────────────────────────────────────
    story.append(HRFlowable(
        width="70%",
        thickness=1.5,
        color=COLOR_GOLD,
        spaceAfter=0.15 * inch,
    ))

    # ── Certificate Title ─────────────────────────────────────────────────────
    story.append(Paragraph(certificate_title, styles["cert_title"]))

    # ── Gold divider line ─────────────────────────────────────────────────────
    story.append(HRFlowable(
        width="70%",
        thickness=1.5,
        color=COLOR_GOLD,
        spaceBefore=0.1 * inch,
        spaceAfter=0.2 * inch,
    ))

    # ── Awarded To Label ──────────────────────────────────────────────────────
    story.append(Paragraph("This certificate is proudly awarded to", styles["awarded_to"]))
    story.append(Spacer(1, 0.05 * inch))

    # ── Recipient Name ────────────────────────────────────────────────────────
    story.append(Paragraph(recipient_name, styles["recipient_name"]))
    story.append(Spacer(1, 0.1 * inch))

    # ── For Completing ────────────────────────────────────────────────────────
    story.append(Paragraph("in recognition of successful completion of", styles["for_completing"]))
    story.append(Spacer(1, 0.05 * inch))

    # ── Event Name ────────────────────────────────────────────────────────────
    story.append(Paragraph(event_name, styles["event_name"]))
    story.append(Spacer(1, 0.15 * inch))

    # ── Gold divider ──────────────────────────────────────────────────────────
    story.append(HRFlowable(
        width="40%",
        thickness=1,
        color=COLOR_GOLD,
        spaceAfter=0.1 * inch,
    ))

    # ── Issue Date ────────────────────────────────────────────────────────────
    story.append(Paragraph(f"Issued on: {issue_date}", styles["issue_date"]))

    # Build PDF with border callback
    doc.build(
        story,
        onFirstPage=draw_certificate_border,
        onLaterPages=draw_certificate_border,
    )

    return output_path
