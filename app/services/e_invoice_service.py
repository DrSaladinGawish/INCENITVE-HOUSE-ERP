import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.models.ihe_models import SalesInvoice, SalesInvoiceLine, Client


ETA_TAX_SCHEMA_ID = "EGS"
ETA_VERSION = "1.0"


def _format_date(d: date | None) -> str:
    return d.isoformat() if d else datetime.now().isoformat()


def _format_decimal(val) -> str:
    d = Decimal(str(val or 0))
    return f"{d:.2f}"


def generate_e_invoice_xml(
    db: Session,
    invoice: SalesInvoice,
    lines: list[SalesInvoiceLine],
    client: Optional[Client] = None,
) -> str:
    inv = ET.Element("Invoice")
    inv.set("xmlns", "urn:eta:egov:xmlschema:1.0")

    doc_id = ET.SubElement(inv, "DocumentID")
    doc_id.text = f"INV-{invoice.InvoiceNumber}"

    issuer = ET.SubElement(inv, "Issuer")
    ET.SubElement(issuer, "Name").text = "IncentiveHouse ERP"
    ET.SubElement(issuer, "ID").text = getattr(invoice, "IssuerID", "IH-ERP-001")
    ET.SubElement(issuer, "TaxID").text = getattr(invoice, "IssuerTaxID", "000-000-000")

    receiver = ET.SubElement(inv, "Receiver")
    if client:
        ET.SubElement(receiver, "Name").text = client.ClientName or ""
        ET.SubElement(receiver, "ID").text = client.ClientCode or ""
        ET.SubElement(receiver, "TaxID").text = getattr(client, "TaxID", "")
    else:
        ET.SubElement(receiver, "Name").text = getattr(invoice, "ClientName", "Unknown")
        ET.SubElement(receiver, "ID").text = getattr(invoice, "ClientCode", "")
        ET.SubElement(receiver, "TaxID").text = ""

    invoice_info = ET.SubElement(inv, "InvoiceInfo")
    ET.SubElement(invoice_info, "InvoiceNumber").text = invoice.InvoiceNumber or ""
    ET.SubElement(invoice_info, "InvoiceDate").text = _format_date(invoice.InvoiceDate)
    ET.SubElement(invoice_info, "Currency").text = invoice.CurrencyCode or "EGP"
    ET.SubElement(invoice_info, "TaxScheme").text = ETA_TAX_SCHEMA_ID
    ET.SubElement(invoice_info, "Version").text = ETA_VERSION
    ET.SubElement(invoice_info, "PaymentMethod").text = getattr(invoice, "PaymentMethod", "") or ""

    doc_type = ET.SubElement(invoice_info, "DocumentType")
    ET.SubElement(doc_type, "Code").text = "I"
    ET.SubElement(doc_type, "Description").text = "Invoice"

    total_amount = Decimal(str(invoice.TotalAmount or 0))
    total_tax = Decimal(str(invoice.TaxAmount or 0))
    net_amount = total_amount - total_tax

    totals = ET.SubElement(inv, "Totals")
    ET.SubElement(totals, "NetAmount").text = _format_decimal(net_amount)
    ET.SubElement(totals, "TaxAmount").text = _format_decimal(total_tax)
    ET.SubElement(totals, "TotalAmount").text = _format_decimal(total_amount)

    items_elem = ET.SubElement(inv, "InvoiceLines")
    for i, line in enumerate(lines, 1):
        line_elem = ET.SubElement(items_elem, "Line")
        ET.SubElement(line_elem, "LineNumber").text = str(i)
        ET.SubElement(line_elem, "Description").text = line.Description or ""
        ET.SubElement(line_elem, "Quantity").text = _format_decimal(line.Quantity or 1)
        ET.SubElement(line_elem, "UnitPrice").text = _format_decimal(line.UnitPrice or 0)

        line_total = Decimal(str(line.Quantity or 1)) * Decimal(str(line.UnitPrice or 0))
        line_tax = Decimal(str(line.TaxAmount or 0)) if hasattr(line, "TaxAmount") and line.TaxAmount else Decimal("0.00")
        line_net = line_total - line_tax

        ET.SubElement(line_elem, "NetAmount").text = _format_decimal(line_net)
        ET.SubElement(line_elem, "TaxAmount").text = _format_decimal(line_tax)

        tax_elem = ET.SubElement(line_elem, "TaxInfo")
        ET.SubElement(tax_elem, "TaxType").text = "T1"
        ET.SubElement(tax_elem, "TaxRate").text = _format_decimal(line.TaxRate or 0) if hasattr(line, "TaxRate") and line.TaxRate else "0.00"
        ET.SubElement(tax_elem, "TaxableAmount").text = _format_decimal(line_total)
        ET.SubElement(tax_elem, "TaxAmount").text = _format_decimal(line_tax)
        ET.SubElement(line_elem, "TotalAmount").text = _format_decimal(line_total)

    rough = ET.tostring(inv, encoding="unicode")
    dom = minidom.parseString(rough)
    return dom.toprettyxml(indent="  ")


def generate_e_invoice_by_number(db: Session, invoice_number: str) -> str | None:
    invoice = db.query(SalesInvoice).filter(SalesInvoice.InvoiceNumber == invoice_number).first()
    if not invoice:
        return None
    lines = db.query(SalesInvoiceLine).filter(SalesInvoiceLine.InvoiceNumber == invoice_number).all()
    client = None
    if invoice.ClientCode:
        client = db.query(Client).filter(Client.ClientCode == invoice.ClientCode).first()
    return generate_e_invoice_xml(db, invoice, lines, client)
