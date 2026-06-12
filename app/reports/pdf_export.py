import io
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Table, Paragraph, Spacer, PageBreak,
    TableStyle, KeepTogether,
)
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from app.reports.pdf_templates import (
    COMPANY_NAME, COMPANY_TAGLINE, MARGIN, PAGE_SIZE,
    title_style, subtitle_style, section_style,
    cell_style, cell_right, cell_center, header_cell,
    total_label_style, total_value_style, footer_style,
    default_table_style,
    COLOR_PRIMARY, COLOR_HEADER_BG, COLOR_HEADER_TEXT,
    COLOR_TOTAL_BG, COLOR_NEGATIVE, COLOR_POSITIVE,
    COLOR_ROW_ALT, COLOR_CONFIDENTIAL,
)


def _format_amount(val) -> str:
    return f"{val:,.2f}"


def _format_date(val) -> str:
    if not val:
        return ""
    if isinstance(val, str):
        return val[:10]
    return val.isoformat()


def _build_doc(title: str) -> SimpleDocTemplate:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=title, author=COMPANY_NAME,
    )
    return doc, buf


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#999999"))
    canvas.drawString(MARGIN, 15 * mm,
        f"{COMPANY_NAME} — {COMPANY_TAGLINE}  |  Page {doc.page}")
    canvas.drawRightString(w - MARGIN, 15 * mm,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.setFont("Helvetica", 42)
    canvas.setFillAlpha(0.04)
    canvas.setFillColor(COLOR_CONFIDENTIAL)
    canvas.saveState()
    canvas.translate(w / 2, h / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "CONFIDENTIAL")
    canvas.restoreState()
    canvas.restoreState()


def _build_story(sections: list[tuple[str, list, str, str]]) -> list:
    story = []
    for section_title, rows, code_label, amount_label in sections:
        story.append(Paragraph(section_title, section_style))
        col_count = 3 if code_label else 4
        data = []
        header_row = []
        if code_label:
            header_row.append(Paragraph("Code", header_cell))
            header_row.append(Paragraph("Name", header_cell))
        else:
            header_row.append(Paragraph("Name", header_cell))
        header_row.append(Paragraph(amount_label or "Amount", header_cell))
        data.append(header_row)
        for r in rows:
            row = []
            if code_label:
                row.append(Paragraph(str(r.get("account_code", "")), cell_center))
                row.append(Paragraph(str(r.get("account_name", "")), cell_style))
            else:
                row.append(Paragraph(str(r.get("name", r.get("narration", ""))), cell_style))
            amt = r.get("amount", r.get("balance", 0))
            amt_str = _format_amount(amt)
            style = cell_right
            if isinstance(amt, (int, float)):
                if amt < 0:
                    amt_str = f"({_format_amount(abs(amt))})"
                    style = cell_right
            row.append(Paragraph(amt_str, style))
            data.append(row)
        tbl = Table(data, colWidths=None, repeatRows=1)
        tbl.setStyle(default_table_style(len(header_row)))
        story.append(tbl)
        story.append(Spacer(1, 4 * mm))
    return story


def trial_balance_pdf(data: dict) -> bytes:
    doc, buf = _build_doc("Trial Balance")
    story = [
        Paragraph("Trial Balance", title_style),
        Paragraph(f"As of {_format_date(data.get('as_of_date'))}", subtitle_style),
    ]
    accounts = data.get("accounts", [])
    if not accounts:
        story.append(Paragraph("No account data available.", cell_style))
    else:
        tb_data = [[Paragraph("Code", header_cell), Paragraph("Account", header_cell),
                     Paragraph("Debit", header_cell), Paragraph("Credit", header_cell),
                     Paragraph("Balance", header_cell)]]
        for a in accounts:
            bal = a.get("balance", 0)
            bal_str = _format_amount(bal)
            if bal < 0:
                bal_str = f"({_format_amount(abs(bal))})"
            tb_data.append([
                Paragraph(str(a.get("account_code", "")), cell_center),
                Paragraph(str(a.get("account_name", "")), cell_style),
                Paragraph(_format_amount(a.get("debit", 0)), cell_right),
                Paragraph(_format_amount(a.get("credit", 0)), cell_right),
                Paragraph(bal_str, cell_right),
            ])
        tb_data.append([
            Paragraph("", cell_style),
            Paragraph("TOTAL", total_label_style),
            Paragraph(_format_amount(data.get("total_debit", 0)), total_value_style),
            Paragraph(_format_amount(data.get("total_credit", 0)), total_value_style),
            Paragraph("", cell_style),
        ])
        tbl = Table(tb_data, colWidths=[55, 220, 80, 80, 80], repeatRows=1)
        tbl.setStyle(default_table_style(5))
        story.append(tbl)
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def profit_loss_pdf(data: dict) -> bytes:
    doc, buf = _build_doc("Profit & Loss Statement")
    story = [
        Paragraph("Profit & Loss Statement", title_style),
        Paragraph(f"{_format_date(data.get('from_date'))} — {_format_date(data.get('to_date'))}", subtitle_style),
    ]
    revenues = data.get("revenues", [])
    expenses = data.get("expenses", [])
    if not revenues and not expenses:
        story.append(Paragraph("No data available for this period.", cell_style))
    else:
        if revenues:
            story.append(Paragraph("Revenues", section_style))
            rev_data = [[Paragraph("Code", header_cell), Paragraph("Account", header_cell),
                         Paragraph("Amount", header_cell)]]
            for r in revenues:
                rev_data.append([
                    Paragraph(str(r.get("account_code", "")), cell_center),
                    Paragraph(str(r.get("account_name", "")), cell_style),
                    Paragraph(_format_amount(r.get("amount", 0)), cell_right),
                ])
            rev_data.append([Paragraph("", cell_style), Paragraph("Total Revenue", total_label_style),
                             Paragraph(_format_amount(data.get("total_revenue", 0)), total_value_style)])
            tbl = Table(rev_data, colWidths=[55, 280, 80], repeatRows=1)
            tbl.setStyle(default_table_style(3))
            story.append(tbl)
        if expenses:
            story.append(Paragraph("Expenses", section_style))
            exp_data = [[Paragraph("Code", header_cell), Paragraph("Account", header_cell),
                         Paragraph("Amount", header_cell)]]
            for e in expenses:
                exp_data.append([
                    Paragraph(str(e.get("account_code", "")), cell_center),
                    Paragraph(str(e.get("account_name", "")), cell_style),
                    Paragraph(_format_amount(e.get("amount", 0)), cell_right),
                ])
            exp_data.append([Paragraph("", cell_style), Paragraph("Total Expenses", total_label_style),
                             Paragraph(_format_amount(data.get("total_expense", 0)), total_value_style)])
            tbl = Table(exp_data, colWidths=[55, 280, 80], repeatRows=1)
            tbl.setStyle(default_table_style(3))
            story.append(tbl)
        ni = data.get("net_income", 0)
        ni_color = COLOR_POSITIVE if ni >= 0 else COLOR_NEGATIVE
        story.append(Spacer(1, 6 * mm))
        net_data = [[Paragraph("Net Income", total_label_style),
                     Paragraph(_format_amount(ni), total_value_style)]]
        tbl = Table(net_data, colWidths=[335, 80])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_TOTAL_BG),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (-1, -1), ni_color),
            ("BOX", (0, 0), (-1, -1), 1, ni_color),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(tbl)
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def balance_sheet_pdf(data: dict) -> bytes:
    doc, buf = _build_doc("Balance Sheet")
    story = [
        Paragraph("Balance Sheet", title_style),
        Paragraph(f"As of {_format_date(data.get('as_of_date'))}", subtitle_style),
    ]
    assets = data.get("assets", [])
    liabilities = data.get("liabilities", [])
    equity = data.get("equity", [])
    if not assets and not liabilities and not equity:
        story.append(Paragraph("No data available.", cell_style))
    else:
        def _section(title, items, total_key, label):
            if not items:
                return
            story.append(Paragraph(title, section_style))
            d = [[Paragraph("Code", header_cell), Paragraph("Account", header_cell),
                  Paragraph("Balance", header_cell)]]
            for it in items:
                bal = it.get("balance", 0)
                bal_str = _format_amount(bal)
                if bal < 0:
                    bal_str = f"({_format_amount(abs(bal))})"
                d.append([
                    Paragraph(str(it.get("account_code", "")), cell_center),
                    Paragraph(str(it.get("account_name", "")), cell_style),
                    Paragraph(bal_str, cell_right),
                ])
            d.append([Paragraph("", cell_style), Paragraph(label, total_label_style),
                      Paragraph(_format_amount(data.get(total_key, 0)), total_value_style)])
            tbl = Table(d, colWidths=[55, 240, 80], repeatRows=1)
            tbl.setStyle(default_table_style(3))
            story.append(tbl)
        _section("Assets", assets, "total_assets", "Total Assets")
        _section("Liabilities", liabilities, "total_liabilities", "Total Liabilities")
        _section("Equity", equity, "total_equity", "Total Equity")
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def cash_flow_pdf(data: dict) -> bytes:
    doc, buf = _build_doc("Cash Flow Statement")
    story = [
        Paragraph("Cash Flow Statement", title_style),
        Paragraph(f"{_format_date(data.get('from_date'))} — {_format_date(data.get('to_date'))}", subtitle_style),
    ]
    cash_accounts = data.get("cash_accounts", [])
    if cash_accounts:
        story.append(Paragraph(
            f"Cash Accounts: {', '.join(a.get('name', a.get('code', '')) for a in cash_accounts)}",
            subtitle_style,
        ))
    sections = [
        ("Operating Activities", data.get("operating", []), "net_operating"),
        ("Investing Activities", data.get("investing", []), "net_investing"),
        ("Financing Activities", data.get("financing", []), "net_financing"),
    ]
    any_data = any(s[1] for s in sections)
    if not any_data and not data.get("opening_balance") and not data.get("closing_balance"):
        story.append(Paragraph("No cash flow data available for this period.", cell_style))
    else:
        for title, items, net_key in sections:
            story.append(Paragraph(title, section_style))
            d = [[Paragraph("Date", header_cell), Paragraph("Narration", header_cell),
                  Paragraph("JV#", header_cell), Paragraph("Amount", header_cell)]]
            for it in items:
                amt = it.get("amount", 0)
                amt_str = _format_amount(amt)
                if amt < 0:
                    amt_str = f"({_format_amount(abs(amt))})"
                d.append([
                    Paragraph(_format_date(it.get("date", "")), cell_center),
                    Paragraph(str(it.get("narration", "")), cell_style),
                    Paragraph(str(it.get("jv_number", "")), cell_center),
                    Paragraph(amt_str, cell_right),
                ])
            net_val = data.get(net_key, 0)
            net_str = _format_amount(net_val)
            if net_val < 0:
                net_str = f"({_format_amount(abs(net_val))})"
            d.append([
                Paragraph("", cell_style), Paragraph("Net", total_label_style),
                Paragraph("", cell_style), Paragraph(net_str, total_value_style),
            ])
            if not items:
                d.append([
                    Paragraph("", cell_style),
                    Paragraph("No transactions", cell_style),
                    Paragraph("", cell_style),
                    Paragraph(_format_amount(0), cell_right),
                ])
            tbl = Table(d, colWidths=[60, 200, 60, 60], repeatRows=1)
            tbl.setStyle(default_table_style(4))
            story.append(tbl)
        story.append(Spacer(1, 4 * mm))
        summary_data = [
            [Paragraph("", cell_style), Paragraph("", cell_style),
             Paragraph("Net Change", total_label_style),
             Paragraph(_format_amount(data.get("net_change", 0)), total_value_style)],
            [Paragraph("", cell_style), Paragraph("", cell_style),
             Paragraph("Opening Balance", total_label_style),
             Paragraph(_format_amount(data.get("opening_balance", 0)), total_value_style)],
            [Paragraph("", cell_style), Paragraph("", cell_style),
             Paragraph("Closing Balance", total_label_style),
             Paragraph(_format_amount(data.get("closing_balance", 0)), total_value_style)],
        ]
        tbl = Table(summary_data, colWidths=[60, 200, 60, 60])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, -1), (-1, -1), COLOR_TOTAL_BG),
            ("FONTNAME", (2, 0), (3, -1), "Helvetica-Bold"),
            ("FONTSIZE", (2, 0), (3, -1), 9),
            ("ALIGN", (2, 0), (3, -1), "RIGHT"),
            ("LINEABOVE", (2, 0), (3, 0), 0.5, colors.HexColor("#d0d0d0")),
            ("LINEBELOW", (2, -1), (3, -1), 1, COLOR_PRIMARY),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
