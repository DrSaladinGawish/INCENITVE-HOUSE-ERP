import hashlib
import os
import csv
import io
import re
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.document import SupportingDocument, DocumentModule


MODULE_SEED_DATA = [
    ("BNK_RECON", "Bank Reconciliation", "Bank/Reconciliation", "Bank reconciliation statements and reports"),
    ("BNK_STMNT", "Bank Statements", "Bank/Statements", "Monthly bank account statements"),
    ("BNK_TRANS", "Bank Transfers", "Bank/Transfers", "Bank transfer confirmations"),
    ("SAL_INV", "Sales Invoices", "Sales/Invoices", "Client sales invoices"),
    ("SAL_QUOT", "Sales Quotations", "Sales/Quotations", "Client quotations and proposals"),
    ("SAL_CN", "Sales Credit Notes", "Sales/CreditNotes", "Sales credit notes and adjustments"),
    ("SAL_PO", "Customer POs", "Sales/POs", "Customer purchase orders"),
    ("PUR_VCH", "Purchase Vouchers", "Purchase/Vouchers", "Vendor purchase vouchers"),
    ("PUR_PO", "Purchase Orders", "Purchase/POs", "Purchase orders to vendors"),
    ("PUR_GRN", "Goods Receipt Notes", "Purchase/GRN", "Goods receipt notes"),
    ("PUR_CN", "Purchase Credit Notes", "Purchase/CreditNotes", "Purchase credit notes"),
    ("EVN_CONTRACT", "Event Contracts", "Events/Contracts", "Event contracts and agreements"),
    ("EVN_WO", "Event Work Orders", "Events/WorkOrders", "Event work orders"),
    ("EVN_BUDGET", "Event Budgets", "Events/Budgets", "Event budget files"),
    ("EVN_PHOTO", "Event Photos", "Events/Photos", "Event photographs and media"),
    ("GL_JV", "Journal Vouchers", "GL/JournalVouchers", "Journal voucher records"),
    ("GL_TB", "Trial Balance", "GL/TrialBalance", "Trial balance reports"),
    ("GL_BS", "Balance Sheet", "GL/BalanceSheet", "Balance sheet reports"),
    ("GL_PL", "Profit & Loss", "GL/ProfitLoss", "Profit and loss statements"),
    ("HR_CONTRACT", "Employment Contracts", "HR/Contracts", "Employee contracts"),
    ("HR_PAYSLIP", "Payslips", "HR/Payslips", "Monthly payslips"),
    ("HR_LEAVE", "Leave Applications", "HR/Leave", "Leave request forms"),
    ("TAX_VAT", "VAT Returns", "Tax/VAT", "VAT return filings"),
    ("TAX_CORP", "Corporate Tax", "Tax/Corporate", "Corporate tax returns"),
    ("LEG_CONTRACT", "Legal Contracts", "Legal/Contracts", "Legal agreements"),
    ("ARC_YEAR", "Year-End Closing", "Archive/YearEnd", "Year-end closing documents"),
    ("ARC_AUDIT", "Audit Reports", "Archive/Audit", "External audit reports"),
    ("ARC_BACKUP", "System Backups", "Archive/Backups", "System backup archives"),
    ("MISC", "Miscellaneous", "Miscellaneous", "Other documents"),
]


def _safe_doc(callback, default=None):
    try:
        return callback()
    except Exception:
        return default


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def seed_modules(self) -> list[DocumentModule]:
        modules = []
        for code, name, folder, desc in MODULE_SEED_DATA:
            existing = _safe_doc(lambda: self.db.execute(
                select(DocumentModule).where(DocumentModule.ModuleCode == code)
            ).scalar_one_or_none())
            if not existing:
                mod = DocumentModule(
                    ModuleCode=code,
                    ModuleName=name,
                    Folder=folder,
                    Description=desc,
                )
                _safe_doc(lambda: self.db.add(mod))
                modules.append(mod)
        _safe_doc(lambda: self.db.commit())
        return modules

    def list_modules(self) -> list[DocumentModule]:
        return _safe_doc(lambda: list(self.db.execute(
            select(DocumentModule).where(DocumentModule.IsActive == True).order_by(DocumentModule.DisplayOrder)
        ).scalars().all()), [])

    def search_documents(
        self,
        query: str | None = None,
        module_code: str | None = None,
        status: str | None = None,
        pnr_number: str | None = None,
        year: int | None = None,
        linked_entity_type: str | None = None,
        verified: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SupportingDocument], int]:
        def _do_search():
            stmt = select(SupportingDocument)
            count_stmt = select(func.count(SupportingDocument.DocumentID))
            if query:
                pattern = f"%{query}%"
                stmt = stmt.where(or_(SupportingDocument.FileName.ilike(pattern), SupportingDocument.Description.ilike(pattern), SupportingDocument.Tags.ilike(pattern)))
                count_stmt = count_stmt.where(or_(SupportingDocument.FileName.ilike(pattern), SupportingDocument.Description.ilike(pattern), SupportingDocument.Tags.ilike(pattern)))
            if module_code:
                stmt = stmt.where(SupportingDocument.ModuleCode == module_code)
                count_stmt = count_stmt.where(SupportingDocument.ModuleCode == module_code)
            if status:
                stmt = stmt.where(SupportingDocument.Status == status)
                count_stmt = count_stmt.where(SupportingDocument.Status == status)
            if pnr_number:
                stmt = stmt.where(SupportingDocument.PNRNumber == pnr_number)
                count_stmt = count_stmt.where(SupportingDocument.PNRNumber == pnr_number)
            if year:
                stmt = stmt.where(SupportingDocument.Year == year)
                count_stmt = count_stmt.where(SupportingDocument.Year == year)
            if linked_entity_type:
                stmt = stmt.where(SupportingDocument.LinkedEntityType == linked_entity_type)
                count_stmt = count_stmt.where(SupportingDocument.LinkedEntityType == linked_entity_type)
            if verified is not None:
                stmt = stmt.where(SupportingDocument.IsVerified == verified)
                count_stmt = count_stmt.where(SupportingDocument.IsVerified == verified)
            total = self.db.execute(count_stmt).scalar() or 0
            stmt = stmt.order_by(SupportingDocument.CreatedAt.desc()).offset(skip).limit(limit)
            items = list(self.db.execute(stmt).scalars().all())
            return items, total
        return _safe_doc(_do_search, ([], 0))

    def get_document(self, doc_id: int) -> SupportingDocument | None:
        return _safe_doc(lambda: self.db.get(SupportingDocument, doc_id))

    def get_stats(self) -> dict:
        def _do_stats():
            total = self.db.execute(select(func.count(SupportingDocument.DocumentID))).scalar() or 0
            verified = self.db.execute(select(func.count(SupportingDocument.DocumentID)).where(SupportingDocument.IsVerified == True)).scalar() or 0
            total_size = self.db.execute(select(func.coalesce(func.sum(SupportingDocument.FileSize), 0))).scalar() or 0
            modules = self.db.execute(select(SupportingDocument.ModuleCode, func.count(SupportingDocument.DocumentID)).group_by(SupportingDocument.ModuleCode)).all()
            return {"total_documents": total, "verified": verified, "unverified": total - verified,
                    "total_size_bytes": int(total_size), "total_size_mb": round(int(total_size) / (1024 * 1024), 2),
                    "module_breakdown": {m[0]: m[1] for m in modules}}
        return _safe_doc(_do_stats, {"total_documents": 0, "verified": 0, "unverified": 0, "total_size_bytes": 0, "total_size_mb": 0, "module_breakdown": {}})

    def get_orphans(self) -> list[SupportingDocument]:
        def _do_orphans():
            return list(self.db.execute(
                select(SupportingDocument).where(SupportingDocument.PNRNumber.is_(None), SupportingDocument.LinkedEntityID.is_(None))
                .order_by(SupportingDocument.CreatedAt.desc())
            ).scalars().all())
        return _safe_doc(_do_orphans, [])

    def verify_document(self, doc_id: int) -> dict:
        doc = self.db.get(SupportingDocument, doc_id)
        if not doc:
            return {"verified": False, "error": "Document not found"}
        if not doc.FilePath or not os.path.exists(doc.FilePath):
            return {"verified": False, "error": "File not found on disk"}
        try:
            sha256 = self._compute_sha256(doc.FilePath)
            match = sha256 == doc.SHA256 if doc.SHA256 else True
            doc.SHA256 = sha256
            doc.IsVerified = True
            self.db.commit()
            return {"verified": True, "sha256": sha256, "match": match, "file_size": os.path.getsize(doc.FilePath)}
        except Exception as e:
            return {"verified": False, "error": str(e)}

    def verify_all(self) -> dict:
        docs = _safe_doc(lambda: list(self.db.execute(select(SupportingDocument)).scalars().all()), [])
        results = {"total": len(docs), "verified": 0, "failed": 0, "missing": 0, "details": []}
        if not docs:
            return results
        for doc in docs:
            if not doc.FilePath or not os.path.exists(doc.FilePath):
                results["missing"] += 1
                results["details"].append({"id": doc.DocumentID, "status": "missing"})
                continue
            try:
                sha256 = self._compute_sha256(doc.FilePath)
                doc.SHA256 = sha256
                doc.IsVerified = True
                results["verified"] += 1
                results["details"].append({"id": doc.DocumentID, "status": "verified"})
            except Exception:
                results["failed"] += 1
                results["details"].append({"id": doc.DocumentID, "status": "error"})
        self.db.commit()
        return results

    def link_document(self, doc_id: int, entity_type: str, entity_id: str, pnr_number: str | None = None) -> dict:
        doc = self.db.get(SupportingDocument, doc_id)
        if not doc:
            return {"linked": False, "error": "Document not found"}
        doc.LinkedEntityType = entity_type
        doc.LinkedEntityID = entity_id
        if pnr_number:
            doc.PNRNumber = pnr_number
        self.db.commit()
        return {"linked": True, "document_id": doc_id, "entity_type": entity_type, "entity_id": entity_id}

    def auto_link(self) -> dict:
        def _do_auto_link():
            docs = list(self.db.execute(
                select(SupportingDocument).where(
                    SupportingDocument.LinkedEntityID.is_(None),
                    SupportingDocument.Status == "active",
                )
            ).scalars().all())
            linked = 0
            skipped = 0
            for doc in docs:
                result = self._try_auto_link(doc)
                if result:
                    linked += 1
                else:
                    skipped += 1
            self.db.commit()
            return {"linked": linked, "skipped": skipped, "total_processed": len(docs)}
        return _safe_doc(_do_auto_link, {"linked": 0, "skipped": 0, "total_processed": 0})

    def _try_auto_link(self, doc: SupportingDocument) -> bool:
        fname = (doc.FileName or "").lower()
        patterns = [
            (r"(PUR[-_]?\d+)", "purchase", "PurchaseVoucher"),
            (r"(SAL[-_]?\d+)", "sales", "SalesInvoice"),
            (r"(GL[-_]?\d+)", "gl", "JournalVoucher"),
            (r"(BNK[-_]?\d+)", "bank", "BankTransaction"),
            (r"(INV[-_]?\d+)", "sales", "SalesInvoice"),
            (r"(VCH[-_]?\d+)", "purchase", "PurchaseVoucher"),
            (r"(JV[-_]?\d+)", "gl", "JournalVoucher"),
        ]
        for pattern, prefix, entity_type in patterns:
            m = re.search(pattern, fname, re.IGNORECASE)
            if m:
                doc.LinkedEntityType = entity_type
                doc.LinkedEntityID = m.group(1).upper()
                return True
        pnr_match = re.search(r"(PNR[-_]?\d+)", fname, re.IGNORECASE)
        if pnr_match:
            doc.PNRNumber = pnr_match.group(1).upper()
            return True
        return False

    def ingest_file(self, filepath: str, module_code: str | None = None) -> dict:
        if not os.path.exists(filepath):
            return {"ingested": False, "error": "File not found"}
        fname = os.path.basename(filepath)
        fsize = os.path.getsize(filepath)
        sha256 = self._compute_sha256(filepath)
        ext = os.path.splitext(fname)[1].lower()
        mime_map = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ".xls": "application/vnd.ms-excel", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ".doc": "application/msword", ".txt": "text/plain", ".csv": "text/csv"}
        mime = mime_map.get(ext, "application/octet-stream")
        pnr_match = re.search(r"(PNR\d+)", fname, re.IGNORECASE)
        pnr = pnr_match.group(1).upper() if pnr_match else None
        year_match = re.search(r"(20\d{2})", fname)
        year = int(year_match.group(1)) if year_match else None
        if not module_code:
            module_code = self._guess_module(fname)
        doc = SupportingDocument(
            FileName=fname,
            FilePath=filepath,
            FileSize=fsize,
            SHA256=sha256,
            MimeType=mime,
            ModuleCode=module_code,
            PNRNumber=pnr,
            Year=year,
            Status="active",
            IsVerified=True,
        )
        self.db.add(doc)
        self.db.commit()
        return {"ingested": True, "document_id": doc.DocumentID, "file_name": fname, "sha256": sha256, "module_code": module_code}

    def ingest_directory(self, directory: str, module_code: str | None = None) -> dict:
        if not os.path.isdir(directory):
            return {"ingested": 0, "errors": 0, "error": "Directory not found"}
        results = {"ingested": 0, "errors": 0, "skipped": 0, "details": []}
        for root, dirs, files in os.walk(directory):
            for fname in files:
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()
                if ext in (".tmp", ".lnk", ".ini"):
                    results["skipped"] += 1
                    continue
                dup = self.db.execute(
                    select(SupportingDocument).where(SupportingDocument.FilePath == fpath)
                ).scalar_one_or_none()
                if dup:
                    results["skipped"] += 1
                    continue
                try:
                    result = self.ingest_file(fpath, module_code)
                    if result.get("ingested"):
                        results["ingested"] += 1
                        results["details"].append({"file": fname, "id": result["document_id"]})
                    else:
                        results["errors"] += 1
                except Exception as e:
                    results["errors"] += 1
                    results["details"].append({"file": fname, "error": str(e)})
        return results

    def ingest_pnr2022(self, archive_path: str | None = None) -> dict:
        base = archive_path or r"D:\Data_Sources\docs\PNR-2022"
        if not os.path.isdir(base):
            return {"ingested": 0, "error": f"PNR-2022 archive not found at {base}"}
        return self.ingest_directory(base, module_code="EVN_CONTRACT")

    def _compute_sha256(self, filepath: str) -> str:
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def upload_file(self, filename: str, content: bytes, module_code: str | None = None, description: str | None = None) -> dict:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = f"{int(datetime.now().timestamp())}_{filename}"
        filepath = os.path.join(upload_dir, safe_name)
        with open(filepath, "wb") as f:
            f.write(content)
        fsize = len(content)
        sha256 = hashlib.sha256(content).hexdigest()
        ext = os.path.splitext(filename)[1].lower()
        mime_map = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ".xls": "application/vnd.ms-excel", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ".doc": "application/msword", ".txt": "text/plain", ".csv": "text/csv"}
        mime = mime_map.get(ext, "application/octet-stream")
        if not module_code:
            module_code = self._guess_module(filename)
        pnr_match = __import__("re").search(r"(PNR\d+)", filename, __import__("re").IGNORECASE)
        pnr = pnr_match.group(1).upper() if pnr_match else None
        year_match = __import__("re").search(r"(20\d{2})", filename)
        year = int(year_match.group(1)) if year_match else None
        doc = SupportingDocument(
            FileName=filename, FilePath=filepath, FileSize=fsize,
            SHA256=sha256, MimeType=mime, ModuleCode=module_code,
            PNRNumber=pnr, Year=year, Description=description,
            Status="active", IsVerified=True,
        )
        self.db.add(doc)
        self.db.commit()
        return {"uploaded": True, "document_id": doc.DocumentID, "file_name": filename}

    def delete_document(self, doc_id: int) -> dict:
        doc = self.db.get(SupportingDocument, doc_id)
        if not doc:
            return {"deleted": False, "error": "Document not found"}
        if doc.FilePath and os.path.exists(doc.FilePath):
            try:
                os.remove(doc.FilePath)
            except OSError:
                pass
        self.db.delete(doc)
        self.db.commit()
        return {"deleted": True, "document_id": doc_id}

    def _guess_module(self, fname: str) -> str:
        fname_lower = fname.lower()
        mapping = [
            (r"(bank|account|statement|recon)", "BNK_RECON"),
            (r"(invoice|sal[-_]?)", "SAL_INV"),
            (r"(purchase|voucher|pur[-_]?)", "PUR_VCH"),
            (r"(contract|agreement)", "EVN_CONTRACT"),
            (r"(budget)", "EVN_BUDGET"),
            (r"(photo|img|image|picture)", "EVN_PHOTO"),
            (r"(journal|jv)", "GL_JV"),
            (r"(trial|balance)", "GL_TB"),
            (r"(payslip|salary|payroll)", "HR_PAYSLIP"),
            (r"(tax|vat)", "TAX_VAT"),
            (r"(legal|attorney)", "LEG_CONTRACT"),
        ]
        for pattern, module in mapping:
            if re.search(pattern, fname_lower):
                return module
        return "MISC"
