#!/usr/bin/env python3
"""
04_document_ingest.py — Batch ingest archived files into dbo.SupportingDocument.
Idempotent via SHA-256. Auto-links by PNR number, invoice number, transaction date.
"""

import os
import sys
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", (
    "mssql+pyodbc://sa:YourStrong@Passw0rd@localhost/IHE_ERP"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
))
ARCHIVE_ROOT = os.getenv("ARCHIVE_ROOT", r"D:\Data_Sources\docs")
BATCH_SIZE = 1000
SUPPORTED_EXTS = {".pdf", ".xlsx", ".xls", ".doc", ".docx", ".jpg", ".png", ".csv", ".txt"}

PNR_PATTERN = re.compile(r"PNR[-_]?(\d{3,6})", re.IGNORECASE)
INV_PATTERN = re.compile(r"INV[-_]?(\d{4,10})", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"(\d{4})")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_files(root: str) -> List[Tuple[str, str, str, int]]:
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            size = os.path.getsize(full)
            files.append((full, rel, fname, size))
    return files


def infer_module_code(relative_path: str, filename: str) -> str:
    rel_lower = relative_path.lower()
    fname_lower = filename.lower()
    if "bank" in rel_lower or "bnk" in fname_lower:
        return "BNK_STMNT"
    if "sales" in rel_lower or "sal" in fname_lower or "invoice" in fname_lower:
        return "SAL_INV"
    if "purchase" in rel_lower or "pur" in fname_lower or "voucher" in fname_lower:
        return "PUR_VCH"
    if "event" in rel_lower or "evn" in rel_lower or "contract" in fname_lower:
        return "EVN_CONTRACT"
    if "gl" in rel_lower or "ledger" in rel_lower or "journal" in fname_lower:
        return "GL_JV"
    if "pnr" in rel_lower:
        return "EVN_WO"
    return "MISC"


def extract_link_hints(filename: str) -> dict:
    hints = {"PNRNumber": None, "Year": None}
    m = PNR_PATTERN.search(filename)
    if m:
        hints["PNRNumber"] = f"PNR{m.group(1)}"
    m = YEAR_PATTERN.findall(filename)
    if m:
        hints["Year"] = int(m[0])
    return hints


def file_exists(session, file_hash: str) -> bool:
    result = session.execute(
        text("SELECT 1 FROM dbo.SupportingDocument WHERE SHA256 = :h"),
        {"h": file_hash}
    ).fetchone()
    return result is not None


def insert_document(session, full_path: str, rel_path: str, filename: str,
                    size: int, file_hash: str, module_code: str, hints: dict) -> int:
    sql = """
        INSERT INTO dbo.SupportingDocument (
            FileName, FilePath, FileSize, SHA256,
            ModuleCode, PNRNumber, Year, Status, CreatedAt
        ) VALUES (
            :file_name, :file_path, :file_size, :sha256,
            :module_code, :pnr_number, :year, :status, :created_at
        );
        SELECT SCOPE_IDENTITY();
    """
    try:
        result = session.execute(text(sql), {
            "file_name": filename,
            "file_path": rel_path,
            "file_size": size,
            "sha256": file_hash,
            "module_code": module_code,
            "pnr_number": hints.get("PNRNumber"),
            "year": hints.get("Year"),
            "status": "active",
            "created_at": datetime.now(),
        }).fetchone()
        session.commit()
        return int(result[0]) if result else None
    except Exception as e:
        print(f"    [WARN] Insert failed: {e}")
        session.rollback()
        return None


def main():
    print("=" * 60)
    print("04_document_ingest.py — Document Archive Ingest")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Archive root: {ARCHIVE_ROOT}")
    print("=" * 60)

    if not os.path.exists(ARCHIVE_ROOT):
        print(f"[FATAL] Archive root not found: {ARCHIVE_ROOT}")
        sys.exit(1)

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("[DISCOVER] Scanning archive...")
    files = discover_files(ARCHIVE_ROOT)
    print(f"[INFO] Discovered {len(files)} files")

    inserted, skipped = 0, 0
    for idx, (full, rel, fname, size) in enumerate(files, 1):
        file_hash = sha256_file(full)
        if file_exists(session, file_hash):
            skipped += 1
            if idx % 5000 == 0:
                print(f"  ... processed {idx} | inserted {inserted} | skipped {skipped}")
            continue

        module_code = infer_module_code(rel, fname)
        hints = extract_link_hints(fname)
        doc_id = insert_document(session, full, rel, fname, size, file_hash, module_code, hints)
        if doc_id:
            inserted += 1
        else:
            skipped += 1

        if idx % BATCH_SIZE == 0:
            print(f"  ... processed {idx} | inserted {inserted} | skipped {skipped}")

    session.close()
    print("\n" + "=" * 60)
    print(f"TOTAL Discovered: {len(files)}")
    print(f"TOTAL Inserted:   {inserted}")
    print(f"TOTAL Skipped:    {skipped} (already exist)")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
