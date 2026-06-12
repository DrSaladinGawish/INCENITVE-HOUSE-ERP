from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import TableStyle

COMPANY_NAME = "IncentiveHouse ERP"
COMPANY_TAGLINE = "Integrated Financial Management System"
PAGE_SIZE = A4
MARGIN = 2 * cm

COLOR_PRIMARY = colors.HexColor("#1e3c72")
COLOR_ACCENT = colors.HexColor("#2a5298")
COLOR_TITLE = colors.HexColor("#1e3c72")
COLOR_HEADER_BG = colors.HexColor("#2a5298")
COLOR_HEADER_TEXT = colors.white
COLOR_ROW_ALT = colors.HexColor("#f0f4f8")
COLOR_TOTAL_BG = colors.HexColor("#e8edf3")
COLOR_TOTAL_TEXT = colors.HexColor("#1e3c72")
COLOR_CONFIDENTIAL = colors.HexColor("#cccccc")
COLOR_NEGATIVE = colors.HexColor("#e74c3c")
COLOR_POSITIVE = colors.HexColor("#27ae60")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ReportTitle", parent=styles["Title"],
    fontSize=18, textColor=COLOR_TITLE, spaceAfter=4 * mm,
    alignment=TA_CENTER, fontName="Helvetica-Bold",
)

subtitle_style = ParagraphStyle(
    "ReportSubtitle", parent=styles["Normal"],
    fontSize=10, textColor=colors.HexColor("#666666"),
    spaceAfter=10 * mm, alignment=TA_CENTER,
)

section_style = ParagraphStyle(
    "SectionTitle", parent=styles["Heading2"],
    fontSize=13, textColor=COLOR_PRIMARY,
    spaceBefore=6 * mm, spaceAfter=4 * mm,
    fontName="Helvetica-Bold",
)

cell_style = ParagraphStyle(
    "CellStyle", parent=styles["Normal"],
    fontSize=8.5, leading=11, fontName="Helvetica",
)

cell_right = ParagraphStyle(
    "CellRight", parent=cell_style,
    alignment=TA_RIGHT,
)

cell_center = ParagraphStyle(
    "CellCenter", parent=cell_style,
    alignment=TA_CENTER,
)

header_cell = ParagraphStyle(
    "HeaderCell", parent=cell_style,
    fontSize=9, fontName="Helvetica-Bold",
    textColor=COLOR_HEADER_TEXT, alignment=TA_CENTER,
)

total_label_style = ParagraphStyle(
    "TotalLabel", parent=cell_style,
    fontSize=9, fontName="Helvetica-Bold",
    textColor=COLOR_TOTAL_TEXT,
)

total_value_style = ParagraphStyle(
    "TotalValue", parent=total_label_style,
    alignment=TA_RIGHT,
)

footer_style = ParagraphStyle(
    "Footer", parent=styles["Normal"],
    fontSize=7, textColor=colors.HexColor("#999999"),
    alignment=TA_CENTER,
)

def default_table_style(col_count: int, total_row: bool = True):
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_HEADER_TEXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d0d0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    cmds.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_ROW_ALT]))
    if total_row:
        cmds.append(("BACKGROUND", (0, -1), (-1, -1), COLOR_TOTAL_BG))
        cmds.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
    return TableStyle(cmds)
