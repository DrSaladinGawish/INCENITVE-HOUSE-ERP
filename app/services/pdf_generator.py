import io, os, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT


def generate_invoice_pdf(invoice_data: dict) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=6)
    elements.append(Paragraph(f"Invoice #{invoice_data.get('invoice_no', 'N/A')}", title_style))
    elements.append(Spacer(1, 6*mm))

    info_style = ParagraphStyle("Info", parent=styles["Normal"], fontSize=10, leading=14)
    elements.append(Paragraph(f"Date: {invoice_data.get('invoice_date', 'N/A')}", info_style))
    elements.append(Paragraph(f"Client: {invoice_data.get('client_name', 'N/A')}", info_style))
    elements.append(Paragraph(f"Due Date: {invoice_data.get('due_date', 'N/A')}", info_style))
    elements.append(Spacer(1, 10*mm))

    table_data = [["Description", "Amount (EGP)"]]
    for item in invoice_data.get("line_items", []):
        table_data.append([item.get("description", ""), f"{item.get('amount', 0):,.2f}"])
    total_style = ParagraphStyle("Total", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold")
    table_data.append([Paragraph("Total", total_style), Paragraph(f"{invoice_data.get('total_amount', 0):,.2f}", ParagraphStyle("TR", parent=total_style, alignment=TA_RIGHT))])

    col_widths = [120*mm, 40*mm]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#324B7F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10*mm))

    if invoice_data.get("notes"):
        elements.append(Paragraph(f"Notes: {invoice_data['notes']}", info_style))

    doc.build(elements)
    buf.seek(0)
    return buf


def generate_pdf_endpoint(invoice_type: str, invoice_id: int, invoice_data: dict) -> io.BytesIO:
    return generate_invoice_pdf(invoice_data)
