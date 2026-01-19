from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Table,
        TableStyle,
        Spacer,
        Image
    )
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime


# ---- Consulting-style palette ----
PRIMARY = colors.HexColor("#111827")   # near-black
SECONDARY = colors.HexColor("#374151") # dark grey
MUTED = colors.HexColor("#6B7280")
LIGHT_BG = colors.HexColor("#F9FAFB")
RISK_BG = colors.HexColor("#FEF2F2")
RISK_TEXT = colors.HexColor("#991B1B")


def build_pdf(
    file_path,
    client,
    story,
    snapshot_rows,
    ceo_moves,
    radar_image_path,
    visual_insight
):
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=36,
        bottomMargin=36
    )

    # ---- Styles ----
    title = ParagraphStyle(
        "title",
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=PRIMARY,
        alignment=1,
        spaceAfter=10
    )

    subtitle = ParagraphStyle(
        "subtitle",
        fontSize=10,
        textColor=MUTED,
        alignment=1,
        spaceAfter=18
    )

    section = ParagraphStyle(
        "section",
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6
    )

    body = ParagraphStyle(
        "body",
        fontSize=10,
        leading=14,
        textColor=SECONDARY,
        spaceAfter=8
    )

    table_cell = ParagraphStyle(
        "table_cell",
        fontSize=9.5,
        leading=13,
        textColor=SECONDARY
    )

    table_header = ParagraphStyle(
        "table_header",
        fontSize=9.5,
        fontName="Helvetica-Bold",
        textColor=PRIMARY
    )

    bullet = ParagraphStyle(
        "bullet",
        fontSize=10,
        leading=14,
        leftIndent=12,
        textColor=SECONDARY,
        spaceAfter=6
    )

    elements = []

    # ---- HEADER ----
    elements.append(Paragraph(f"{client} – Executive Team Diagnostic", title))
    elements.append(Paragraph(
        "<i>Why this matters:</i> To understand how the executive team’s behaviour is helping or hindering execution of the current strategy.",
        subtitle
    ))

    # ---- TEAM STORY ----
    elements.append(Paragraph("Team Story", section))
    elements.append(Paragraph(story, body))

    # ---- SNAPSHOT TABLE ----
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("TEAMS Dimension Snapshot", section))

    table_data = [
        [
            Paragraph("Dimension", table_header),
            Paragraph("Status", table_header),
            Paragraph("What this means", table_header)
        ]
    ]

    for dim, status, note in snapshot_rows:
        table_data.append([
            Paragraph(dim, table_cell),
            Paragraph(status, table_cell),
            Paragraph(note, table_cell)
        ])

    table = Table(
        table_data,
        colWidths=[110, 70, 260],  # FIXED widths = no overflow
        hAlign="LEFT",
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

        # Risk emphasis
        ("BACKGROUND", (1, 1), (1, -1), RISK_BG),
        ("TEXTCOLOR", (1, 1), (1, -1), RISK_TEXT),
    ]))

    elements.append(table)

    # ---- VISUAL ----
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("TEAMS Visual Snapshot", section))

    img = Image(radar_image_path, width=230, height=230)
    img.hAlign = "CENTER"
    elements.append(img)

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        visual_insight,
        body
    ))


    # ---- CEO MOVES ----
    elements.append(Spacer(1, 14))
    doc.build(elements)


