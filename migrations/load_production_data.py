#!/usr/bin/env python3
"""
load_production_data.py — Load real USB data into IHE_ERP SQL Server.
Sources:
  - Client Master Data Registery.xlsx (Customer - Vendor Index)
  - Incentive House Fullmodules.xlsx (COA, Service Type, PNR, Bank, Sales, Purchases)

Idempotent: skips existing records by natural key.
Run inside Docker: docker compose exec api python migrations/load_production_data.py
"""

import os, sys, re
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Use settings from the app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings

DATABASE_URL = settings.SYNC_DATABASE_URL

# Data paths (copied to project dir for Docker access)
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "production"
REGISTRY_PATH = DATA_DIR / "Client Master Data Registery.xlsx"
FULLMODULES_PATH = DATA_DIR / "Incentive House Fullmodules.xlsx"

BATCH_SIZE = 200


def safe(val):
    if pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val.date()
    s = str(val).strip()
    return s if s else None


def safe_float(val):
    if pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    if pd.isna(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def db_date(val):
    if val is None:
        return None
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
        return None
    if hasattr(val, 'date'):
        return val.date() if hasattr(val, 'date') else val
    return val


def exists(session, table, conditions):
    where = " AND ".join(f"{k} = :{k}" for k in conditions)
    sql = f"SELECT 1 FROM {table} WHERE {where}"
    return session.execute(text(sql), conditions).fetchone() is not None


def insert(session, table, data, key_cols):
    if not data:
        return 0, 0
    inserted = 0
    skipped = 0
    for row in data:
        try:
            # Check if exists
            keys = {k: row[k] for k in key_cols if k in row and row[k] is not None}
            if keys:
                if exists(session, table, keys):
                    skipped += 1
                    continue
            cols = [k for k, v in row.items() if v is not None]
            if not cols:
                skipped += 1
                continue
            ph = [f":{c}" for c in cols]
            sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(ph)})"
            session.execute(text(sql), {c: row[c] for c in cols})
            inserted += 1
            if inserted % BATCH_SIZE == 0:
                session.commit()
                print(f"  ... committed {inserted}")
        except Exception as e:
            print(f"  [WARN] {e}")
            skipped += 1
    session.commit()
    return inserted, skipped


def load_clients_vendors(session):
    print("\n=== Loading Client/Vendor/Staff/Bank Registry ===")
    df = pd.read_excel(REGISTRY_PATH, sheet_name="Customer - Vendor Index")
    print(f"  Read {len(df)} rows from registry")

    clients = []
    vendors = []
    employees = []
    banks = []

    for _, r in df.iterrows():
        code = safe(r.get("Customer - Vendor Code "))
        name = safe(r.get("Customer - Vendor  Name  "))
        rel = safe(r.get("Relationship Type"))
        if not code or not name:
            continue

        address = safe(r.get("Address"))
        phone = safe(r.get("Telephone Number "))
        email = safe(r.get("Email Addres"))
        contact = safe(r.get("Contact Person "))
        tax_id = safe(r.get("TAX ID"))
        tax_reg = safe(r.get("TAX Register Number "))
        posting = safe(r.get("Posting Account"))
        pay_terms = safe(r.get("Payment Terms"))
        bank_name = safe(r.get("Bank Name "))
        branch = safe(r.get("Branch "))
        egp_acc = safe(r.get("EGP Account Number "))
        usd_acc = safe(r.get("USD Account Number 2"))
        iban = safe(r.get("IBAN"))

        if rel and "client" in rel.lower():
            clients.append({
                "ClientCode": code, "ClientName": name,
                "Address": address, "Telephone": phone, "Email": email,
                "ContactPerson": contact, "TaxID": tax_id, "TaxRegisterNo": tax_reg,
                "PostingAccount": posting, "PaymentTerms": pay_terms,
                "IsActive": 1,
            })
        elif rel and "vendor" in rel.lower():
            vendors.append({
                "VendorCode": code, "VendorName": name,
                "Address": address, "Telephone": phone, "Email": email,
                "TaxID": tax_id, "TaxRegisterNo": tax_reg,
                "PostingAccount": posting, "PaymentTerms": pay_terms,
                "BankName": bank_name, "Branch": branch,
                "EGPAccountNo": egp_acc, "USDAccountNo": usd_acc, "IBAN": iban,
                "VendorType": rel,
                "IsActive": 1,
            })
        elif rel and "staff" in rel.lower():
            emp_type = "Staff"
            if "owner" in rel.lower():
                emp_type = "Owner"
            employees.append({
                "EmployeeCode": code, "EmployeeName": name,
                "EmployeeType": emp_type,
                "PostingAccount": posting,
                "IsActive": 1,
            })
        elif rel and "bank" in rel.lower():
            post_acc = posting
            gl_acc = None
            if posting:
                gl_acc = posting
            banks.append({
                "BankCode": code, "BankName": name,
                "GLAccount": gl_acc,
                "IsActive": 1,
            })

    i_cli, s_cli = insert(session, "dbo.Client", clients, ["ClientCode"])
    i_ven, s_ven = insert(session, "dbo.Vendor", vendors, ["VendorCode"])
    i_emp, s_emp = insert(session, "dbo.Employee", employees, ["EmployeeCode"])
    i_bnk, s_bnk = insert(session, "dbo.Bank", banks, ["BankCode"])
    print(f"  Clients: {i_cli} inserted, {s_cli} skipped")
    print(f"  Vendors: {i_ven} inserted, {s_ven} skipped")
    print(f"  Employees: {i_emp} inserted, {s_emp} skipped")
    print(f"  Banks: {i_bnk} inserted, {s_bnk} skipped")


def read_sheet(session, sheet_name, header_row, skip_rows_before=None):
    """Read xlsx with known header row, stripping whitespace from column names."""
    if skip_rows_before is not None:
        df = pd.read_excel(FULLMODULES_PATH, sheet_name=sheet_name, skiprows=skip_rows_before, header=None)
    else:
        df = pd.read_excel(FULLMODULES_PATH, sheet_name=sheet_name, header=None)
    # The header is at position header_row (0-indexed)
    headers = [str(v).strip() if pd.notna(v) else f"col{i}" for i, v in enumerate(df.iloc[header_row])]
    df = df.iloc[header_row + 1:].reset_index(drop=True)
    df.columns = headers
    # Remove empty columns (where first col has no name)
    df = df.drop(columns=[c for c in df.columns if c.startswith("col")], errors='ignore')
    return df


def load_coa(session):
    print("\n=== Loading Chart of Accounts ===")
    df = read_sheet(session, "COA", header_row=3)
    print(f"  Read {len(df)} rows, columns: {list(df.columns)}")

    accounts = []
    for _, r in df.iterrows():
        code = safe(r.get("Account Code"))
        name = safe(r.get("Account Name"))
        acc_type = safe(r.get("Account Category"))
        sub_cat = safe(r.get("Account Subcategory"))
        model = safe(r.get("Related Model"))
        if not code or not name:
            continue
        segments = code.split("-")
        parent = "-".join(segments[:-1]) if len(segments) > 1 else None
        acc_type_det = acc_type or sub_cat or code.split("-")[0]
        accounts.append({
            "AccountCode": code,
            "AccountName": name,
            "AccountType": (acc_type_det[:50] if acc_type_det else code.split("-")[0])[:50],
            "ParentAccount": parent,
            "IsControlAccount": 0,
            "CurrencyCode": "EGP",
        })

    i, s = insert(session, "dbo.ChartOfAccounts", accounts, ["AccountCode"])
    print(f"  COA: {i} inserted, {s} skipped")


def load_service_types(session):
    print("\n=== Loading Service Types ===")
    df = read_sheet(session, "Service Type Index", header_row=2)
    print(f"  Read {len(df)} rows, columns: {list(df.columns)}")

    svc = []
    for _, r in df.iterrows():
        code = safe(r.get("Code"))
        name = safe(r.get("Narration"))
        cost_acc = safe(r.get("Cost Accounts"))
        rev_acc = safe(r.get("Revenue Account"))
        if code and name and code.startswith("T-"):
            svc.append({
                "ServiceTypeCode": code,
                "ServiceName": name,
                "CostAccount": cost_acc,
            })

    i, s = insert(session, "dbo.ServiceType", svc, ["ServiceTypeCode"])
    print(f"  Service Types: {i} inserted, {s} skipped")


def load_pnrs(session):
    print("\n=== Loading PNRs ===")
    try:
        df = read_sheet(session, "PNR INDIX", header_row=4)
        print(f"  Read {len(df)} rows, columns: {list(df.columns)}")
    except Exception as e:
        print(f"  [SKIP] Cannot read PNR INDIX: {e}")
        return

    pnrs = []
    for _, r in df.iterrows():
        wo = safe(r.get("Work Order Number"))
        if not wo:
            continue
        client_code = safe(r.get("Customer Code"))
        event_name = safe(r.get("Event -Title"))
        ref = safe(r.get("Customer Refrance Number"))
        doc_date = safe(r.get("Document Date"))
        amount = safe_float(r.get("Amount"))

        year = None
        if doc_date:
            d = db_date(doc_date)
            if d:
                year = d.year

        pnrs.append({
            "PNRNumber": wo,
            "ClientCode": client_code,
            "EventName": event_name,
            "JobFolder": ref,
            "Year": year,
            "Status": "Active",
            "CurrencyCode": "EGP",
        })

    i, s = insert(session, "dbo.PNRMaster", pnrs, ["PNRNumber"])
    print(f"  PNRs: {i} inserted, {s} skipped")


def load_bank_transactions(session):
    print("\n=== Loading Bank Transactions ===")
    df = read_sheet(session, "BANK Transactions", header_row=2)
    print(f"  Read {len(df)} rows, columns: {list(df.columns)}")

    txns = []
    for _, r in df.iterrows():
        txn_date = safe(r.get("Date"))
        if not txn_date:
            continue
        payee = safe(r.get("In favour of"))
        doc_type = safe(r.get("Document Type"))
        doc_num = safe(r.get("Document Number1"))
        withdrawal = safe_float(r.get("Withdrawal"))
        deposit = safe_float(r.get("Deposits"))
        balance = safe_float(r.get("Balance"))
        txn_type = safe(r.get("Transaction Type"))
        jv_num = safe(r.get("JVNumber"))
        narration = safe(r.get("Narration"))
        dr_acc = safe(r.get("Dr.Account"))
        cr_acc = safe(r.get("Cr.Account"))
        from_sub = safe(r.get("From SUB Categ"))
        to_sub = safe(r.get("To SUB Categ"))

        # Map bank names to codes
        bank_code = from_sub
        if bank_code:
            bank_map = {
                "emirates nbad bank": "B-0001",
                "cib": "B-0002", "hsbc": "B-0003",
                "qnb": "B-0004", "aaib": "B-0005",
            }
            bl = bank_code.lower().strip()
            for k, v in bank_map.items():
                if k in bl:
                    bank_code = v
                    break

        # Truncate long strings to fit DB column sizes (VARCHAR(20) max)
        if dr_acc and len(dr_acc) > 20: dr_acc = dr_acc[:20]
        if cr_acc and len(cr_acc) > 20: cr_acc = cr_acc[:20]
        if from_sub and len(from_sub) > 20: from_sub = from_sub[:20]
        if to_sub and len(to_sub) > 20: to_sub = to_sub[:20]

        txns.append({
            "TransactionDate": txn_date,
            "Payee": payee,
            "DocumentType": doc_type,
            "DocumentNumber": doc_num,
            "Withdrawal": withdrawal,
            "Deposit": deposit,
            "RunningBalance": balance,
            "TransactionType": txn_type or ("Deposit" if (deposit or 0) > 0 else "Withdrawal"),
            "JVNumber": jv_num,
            "Narration": narration,
            "DrAccount": dr_acc,
            "CrAccount": cr_acc,
            "FromSubCategory": from_sub,
            "ToSubCategory": to_sub,
            "BankCode": bank_code,
            "CurrencyCode": "EGP",
        })

    i, s = insert(session, "dbo.BankTransaction", txns, ["TransactionDate", "DocumentNumber", "Withdrawal", "Deposit"])
    print(f"  Bank Transactions: {i} inserted, {s} skipped")


def ensure_pnr(session, pnr_number, client_code=None, event_name=None):
    """Create a minimal PNRMaster record if it doesn't exist."""
    if not pnr_number:
        return
    sql = "SELECT COUNT(*) FROM dbo.PNRMaster WHERE PNRNumber = :pn"
    cnt = session.execute(text(sql), {"pn": pnr_number}).scalar()
    if cnt and cnt > 0:
        return
    data = {"PNRNumber": pnr_number, "Status": "Active", "CurrencyCode": "EGP"}
    if client_code:
        data["ClientCode"] = client_code
    if event_name:
        data["EventName"] = event_name
    cols = list(data.keys())
    ph = [f":{c}" for c in cols]
    session.execute(text(f"INSERT INTO dbo.PNRMaster ({', '.join(cols)}) VALUES ({', '.join(ph)})"), data)
    session.commit()
    print(f"  [INFO] Created PNR record: {pnr_number}")


def load_sales(session):
    print("\n=== Loading Sales Invoices ===")
    df = read_sheet(session, "Sales Ladger ", header_row=1)
    print(f"  Read {len(df)} rows, columns: {list(df.columns)}")

    invoices = []
    for _, r in df.iterrows():
        inv_num = safe(r.get("Invoice Number"))
        if not inv_num:
            continue
        pnr = safe(r.get("PNR"))
        # Skip values that look like dates (contain "00:00:00" or match date pattern)
        if pnr:
            import re
            if re.search(r'\d{2}:\d{2}:\d{2}', str(pnr)) or re.match(r'^\d{4}[-\/]\d{1,2}[-\/]\d{1,2}', str(pnr)):
                pnr = None
        client = safe(r.get("Client Code"))
        event = safe(r.get("Event  Name"))
        inv_date = db_date(safe(r.get("Invoice Date")))
        due_date = db_date(safe(r.get("Due Date")))
        collected = safe_float(r.get("Collected Amount"))
        ps_raw = safe(r.get("Paid /Unpaid"))
        total = safe_float(r.get("Total Invoice Value"))
        if ps_raw:
            ps = ps_raw.lower().strip()
            if "paid" in ps:
                ps_val = "Paid"
            elif "unpaid" in ps or not ps:
                ps_val = "Unpaid"
            else:
                ps_val = ps_raw.strip()
        else:
            ps_val = "Unpaid"

        if pnr and client:
            ensure_pnr(session, pnr, client, event)

        invoices.append({
            "InvoiceNumber": inv_num,
            "PNRNumber": pnr,
            "ClientCode": client,
            "EventName": event,
            "InvoiceDate": inv_date,
            "DueDate": due_date,
            "TotalValue": total,
            "CollectedAmount": collected or 0,
            "PaymentStatus": ps_val,
            "CurrencyCode": "EGP",
        })

    inserted = 0
    skipped = 0
    for inv in invoices:
        try:
            inv_num = inv["InvoiceNumber"]
            if inv_num:
                sql = "SELECT COUNT(*) as cnt FROM dbo.SalesInvoice WHERE InvoiceNumber = :inv"
                res = session.execute(text(sql), {"inv": inv_num}).scalar()
                if res and res > 0:
                    skipped += 1
                    continue
            cols = [k for k, v in inv.items() if v is not None]
            ph = [f":{c}" for c in cols]
            sql = f"INSERT INTO dbo.SalesInvoice ({', '.join(cols)}) VALUES ({', '.join(ph)})"
            session.execute(text(sql), {c: inv[c] for c in cols})
            inserted += 1
            if inserted % BATCH_SIZE == 0:
                session.commit()
                print(f"  ... committed {inserted}")
        except Exception as e:
            print(f"  [WARN] {e}")
            skipped += 1
    session.commit()
    print(f"  Sales Invoices: {inserted} inserted, {skipped} skipped")


def load_purchases(session):
    print("\n=== Loading Purchase Vouchers ===")
    df = read_sheet(session, "PUR Ladger ", header_row=1)
    print(f"  Read {len(df)} rows, columns: {list(df.columns)}")

    # Build vendor name -> code map (exact match only)
    ven_rows = session.execute(text("SELECT VendorCode, VendorName FROM dbo.Vendor")).fetchall()
    ven_map = {}
    next_vendor_num = 19
    for vc, vn in ven_rows:
        if vn:
            ven_map[vn.strip().lower()] = vc
            num = int(vc.split("-")[1])
            if num >= next_vendor_num:
                next_vendor_num = num + 1

    def resolve_vendor(name):
        if not name:
            return None
        nm = name.strip().lower()
        if nm in ven_map:
            return ven_map[nm]
        nonlocal next_vendor_num
        new_code = f"V-{next_vendor_num:04d}"
        next_vendor_num += 1
        try:
            session.execute(
                text("INSERT INTO dbo.Vendor (VendorCode, VendorName, IsActive) VALUES (:c, :n, 1)"),
                {"c": new_code, "n": name.strip()}
            )
            session.commit()
            ven_map[nm] = new_code
            print(f"  [INFO] Created vendor {new_code}: {name.strip()}")
        except Exception as e:
            print(f"  [WARN] Could not create vendor {new_code}: {e}")
            return None
        return new_code

    # Build service type name -> code map
    st_rows = session.execute(text("SELECT ServiceTypeCode, ServiceName FROM dbo.ServiceType")).fetchall()
    st_map = {}
    for sc, sn in st_rows:
        if sn:
            st_map[sn.strip().lower()] = sc

    def resolve_service_type(name):
        if not name:
            return None
        nm = name.strip().lower()
        # exact match
        if nm in st_map:
            return st_map[nm]
        # substring match: find service type whose name is contained in or contains the value
        for k, v in st_map.items():
            if k in nm or nm in k:
                return v
        return None

    # Group rows by voucher number
    voucher_groups = {}
    for _, r in df.iterrows():
        vnum = safe(r.get("PUR-Vocher #"))
        if not vnum:
            continue
        sub_total = safe_float(r.get("Sub Total"))
        if not sub_total or sub_total == 0:
            continue  # skip empty lines
        if vnum not in voucher_groups:
            voucher_groups[vnum] = {
                "DocumentNumber": safe(r.get("Document Number")),
                "PNRNumber": safe(r.get("PNR-Number")),
                "EventName": safe(r.get("Event  Name")),
                "InvoiceDate": db_date(safe(r.get("invoice Date"))),
                "lines": [],
            }
        ven_name = safe(r.get("Vendor Name"))
        st_name = safe(r.get("Service Type"))
        voucher_groups[vnum]["lines"].append({
            "ServiceType": resolve_service_type(st_name),
            "VendorCode": resolve_vendor(ven_name),
            "ItemNarration": safe(r.get("Item Narration")),
            "Quantity": safe_float(r.get("Units/PAX")),
            "NoOfNights": safe_int(r.get("no of \nnights")),
            "UnitPrice": safe_float(r.get("Unit Price")),
            "SubTotal": safe_float(r.get("Sub Total")),
            "VATAmount": safe_float(r.get("col_15")),  # col_15 may be VAT
        })

    inserted_v = 0
    skipped_v = 0
    inserted_l = 0
    # Get any existing voucher IDs for vouchers that have no lines yet
    existing = {}
    rows = session.execute(text("SELECT VoucherNumber, VoucherID FROM dbo.PurchaseVoucher")).fetchall()
    existing = {r[0]: r[1] for r in rows}

    for vnum, g in voucher_groups.items():
        try:
            vid = None
            if vnum in existing:
                # Check if lines already exist
                cnt = session.execute(text("SELECT COUNT(*) FROM dbo.PurchaseVoucherLine WHERE VoucherID = :vid"), {"vid": existing[vnum]}).scalar()
                if cnt and cnt > 0:
                    skipped_v += 1
                    continue
                vid = existing[vnum]
            else:
                total = sum((l["SubTotal"] or 0) for l in g["lines"])
                pnr = g["PNRNumber"]
                if pnr:
                    ensure_pnr(session, pnr, event_name=g["EventName"])
                voucher_data = {
                    "VoucherNumber": vnum,
                    "DocumentNumber": g["DocumentNumber"],
                    "PNRNumber": pnr,
                    "EventName": g["EventName"],
                    "InvoiceDate": g["InvoiceDate"],
                    "TotalValue": total,
                    "CurrencyCode": "EGP",
                }
                cols = [k for k, v in voucher_data.items() if v is not None]
                ph = [f":{c}" for c in cols]
                # Use OUTPUT INSERTED to get the new ID directly
                sql = f"INSERT INTO dbo.PurchaseVoucher ({', '.join(cols)}) OUTPUT INSERTED.VoucherID VALUES ({', '.join(ph)})"
                vid = session.execute(text(sql), {c: voucher_data[c] for c in cols}).scalar()
                if not vid:
                    print(f"  [WARN] No VoucherID returned for {vnum}")
                    skipped_v += 1
                    continue

            # Insert lines
            for line in g["lines"]:
                line_data = {
                    "VoucherID": vid,
                    "ServiceTypeCode": line["ServiceType"],
                    "VendorCode": line["VendorCode"],
                    "ItemNarration": line["ItemNarration"],
                    "Quantity": line["Quantity"],
                    "NoOfNights": line["NoOfNights"],
                    "UnitPrice": line["UnitPrice"],
                    "SubTotal": line["SubTotal"],
                    "VATAmount": line["VATAmount"],
                }
                lcols = [k for k, v in line_data.items() if v is not None]
                lph = [f":{c}" for c in lcols]
                sql = f"INSERT INTO dbo.PurchaseVoucherLine ({', '.join(lcols)}) VALUES ({', '.join(lph)})"
                session.execute(text(sql), {c: line_data[c] for c in lcols})
                inserted_l += 1

            inserted_v += 1
            if inserted_v % BATCH_SIZE == 0:
                session.commit()
                print(f"  ... committed {inserted_v} vouchers")
        except Exception as e:
            print(f"  [WARN] Voucher {vnum}: {e}")
            skipped_v += 1
    session.commit()
    print(f"  Purchase Vouchers: {inserted_v} inserted, {skipped_v} skipped, {inserted_l} lines")


def main():
    print("=" * 60)
    print("Production Data Loader — IHE_ERP")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    if not REGISTRY_PATH.exists():
        print(f"[FATAL] Registry not found: {REGISTRY_PATH}")
        sys.exit(1)
    if not FULLMODULES_PATH.exists():
        print(f"[FATAL] Fullmodules not found: {FULLMODULES_PATH}")
        sys.exit(1)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        load_clients_vendors(session)
        load_coa(session)
        load_service_types(session)
        load_pnrs(session)
        load_bank_transactions(session)
        load_sales(session)
        load_purchases(session)
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("Done. Run verify: docker compose exec api python migrations/06_verify.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
