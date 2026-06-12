r"""
USB Archive Scanner v1.0 — IncentiveHouse ERP
Scans D:\IncentiveHouse_ERP\USB Drive, deduplicates, classifies, generates report.
"""
import json, hashlib, os, re, time, csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict

USB_ROOT = Path("D:/IncentiveHouse_ERP/USB Drive")
OUTPUT_DIR = Path("D:/IncentiveHouse_ERP/reports")
OUTPUT_DIR.mkdir(exist_ok=True)

DOC_TYPES = {
    "invoice": r"(?i)(inv\s*|invoice|e-invoice|einvoice|sales)",
    "purchase": r"(?i)(pur|purchase|po\s*|order|buy)",
    "banking": r"(?i)(bnk|bank|statement|recon|ledger)",
    "payment": r"(?i)(payment|voucher|pv\s*)",
    "tax": r"(?i)(vat|tax|eta|return)",
    "client": r"(?i)(client|customer|soa|statement)",
    "vendor": r"(?i)(vendor|supplier)",
    "contract": r"(?i)(contract|agreement|mom)",
    "payroll": r"(?i)(payroll|salary|hr\s*|staff|employee)",
    "financial": r"(?i)(financial|pl\s*|bs\s*|tb\s*|balance|profit)",
    "legal": r"(?i)(legal|license|trade|commercial)",
    "photo": r"(?i)(photo|image|scan|jpeg|jpg|png)",
    "report": r"(?i)(report|summary|analysis)",
    "backup": r"(?i)(backup|accdb|mdb|database)",
}
DEFAULT_TYPE = "unclassified"

JS_VENDOR_EXTS = {".js", ".ts", ".map", ".mjs", ".cjs", ".d.ts", ".tsbuildinfo"}
JS_VENDOR_DIRS = {"node_modules", ".npm", ".yarn", ".cache", "__pycache__", "lib", "dist", "build"}


def classify_file(rel_path: str) -> str:
    name = Path(rel_path).name
    for doc_type, pattern in DOC_TYPES.items():
        if re.search(pattern, name):
            return doc_type
    ext = Path(name).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}:
        return "photo"
    if ext in {".pdf"}:
        return "pdf"
    if ext in {".xlsx", ".xls", ".csv"}:
        return "spreadsheet"
    if ext in {".docx", ".doc", ".txt"}:
        return "document"
    return DEFAULT_TYPE


def is_vendor_js(path: Path, rel_path: str) -> bool:
    """Check if a JS/TS file is vendor/build artifact."""
    if path.suffix.lower() not in JS_VENDOR_EXTS:
        return False
    for part in path.parts:
        if part in JS_VENDOR_DIRS:
            return True
    # Check for common vendor patterns in path
    vendor_patterns = [r"/vendors?/", r"/dist/", r"/build/", r"/_bundles/"]
    if any(re.search(p, rel_path.replace("\\", "/")) for p in vendor_patterns):
        return True
    return False


def scan():
    print(f"Scanning {USB_ROOT} ...")
    start = time.time()

    if not USB_ROOT.exists():
        print(f"ERROR: {USB_ROOT} does not exist")
        return

    all_files = list(USB_ROOT.rglob("*"))
    all_files = [f for f in all_files if f.is_file()]
    total = len(all_files)
    print(f"Found {total} files ({total/1024/1024*0:.0f} MB)")

    index = []
    size_total = 0
    vendors = []
    by_type = defaultdict(list)
    hash_map = {}
    dup_groups = defaultdict(list)
    skip_exts = {".pyc", ".pyo", ".DS_Store", ".gitkeep", ".gitignore"}

    for i, fp in enumerate(all_files):
        if i % 5000 == 0 and i > 0:
            print(f"  ... {i}/{total}")
        try:
            size = fp.stat().st_size
        except OSError:
            continue
        if size == 0 and fp.suffix.lower() not in {".txt", ".csv", ".log", ".pdf", ".xlsx", ".xls", ".docx", ".doc"}:
            continue  # Skip empty non-content files

        rel = fp.relative_to(USB_ROOT).as_posix()

        # Classify vendor JS
        if is_vendor_js(fp, rel):
            vendors.append({"path": rel, "size": size})
            continue

        size_total += size
        ext = fp.suffix.lower()
        if ext in skip_exts:
            continue

        # Hash
        try:
            h = hashlib.md5()
            with open(fp, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            md5 = h.hexdigest()
        except PermissionError:
            md5 = ""

        doc_type = classify_file(rel)
        entry = {
            "path": rel,
            "size": size,
            "ext": ext,
            "md5": md5,
            "type": doc_type,
            "modified": datetime.fromtimestamp(fp.stat().st_mtime).isoformat(),
        }
        index.append(entry)
        by_type[doc_type].append(entry)

        if md5:
            hash_map.setdefault(md5, []).append(entry)
            if len(hash_map[md5]) > 1:
                dup_groups[md5] = hash_map[md5]

    elapsed = time.time() - start

    vendor_waste = sum(v["size"] for v in vendors)
    vendor_count = len(vendors)
    dup_waste = sum(e["size"] for g in dup_groups.values() for e in g) - sum(
        min(e["size"] for e in g) for g in dup_groups.values()
    )
    dup_count = sum(len(g) - 1 for g in dup_groups.values()) if dup_groups else 0

    report = {
        "scan_time": datetime.now().isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "usb_root": str(USB_ROOT),
        "summary": {
            "total_files": len(index),
            "total_size_mb": round(size_total / 1048576, 1),
            "vendor_js_files": vendor_count,
            "vendor_js_waste_mb": round(vendor_waste / 1048576, 1),
            "duplicate_groups": len(dup_groups),
            "duplicate_excess_files": dup_count,
            "duplicate_waste_mb": round(dup_waste / 1048576, 1),
        },
        "by_type": {t: len(files) for t, files in sorted(by_type.items(), key=lambda x: -len(x[1]))},
        "extensions": {},
        "vendors": vendors,
        "index": index,
        "duplicates": {md5: [e["path"] for e in entries] for md5, entries in dup_groups.items()},
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"usb_scan_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Saved JSON: {json_path}")

    # HTML report
    html_path = OUTPUT_DIR / f"usb_scan_{ts}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        _write_html(f, report)
    print(f"Saved HTML: {html_path}")

    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE — {elapsed:.1f}s")
    print(f"  Business files: {len(index)} ({round(size_total/1048576,1)} MB)")
    print(f"  Vendor JS waste: {vendor_count} files ({round(vendor_waste/1048576,1)} MB) — EXCLUDED")
    print(f"  Duplicate excess: {dup_count} files ({round(dup_waste/1048576,1)} MB)")
    print(f"  Types: {len(by_type)} categories")
    print(f"{'='*60}")
    return report


def _write_html(f, report):
    s = report["summary"]
    f.write(f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><title>USB Archive Scanner Report</title>
<style>
body{{font-family:-apple-system,sans-serif;margin:20px;background:#f5f5f5;color:#222}}
h1{{color:#1a237e}}
.card{{background:#fff;border-radius:8px;padding:16px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,0.12)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
.stat{{text-align:center;padding:12px;background:#e8eaf6;border-radius:6px}}
.stat .num{{font-size:24px;font-weight:bold;color:#1a237e}}
.stat .lbl{{font-size:12px;color:#666}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#1a237e;color:#fff;padding:8px;text-align:left}}
td{{padding:6px 8px;border-bottom:1px solid #e0e0e0}}
.danger{{color:#c62828}}
.warn{{color:#e65100}}
.ok{{color:#2e7d32}}
tr:hover{{background:#f5f5f5}}
.dedup{{background:#fff3e0}}
</style></head><body>
<h1>📀 USB Archive Scanner Report</h1>
<p>Scanned: {report['scan_time']} | Elapsed: {report['elapsed_seconds']}s</p>
<div class="card grid">
<div class="stat"><div class="num">{s['total_files']}</div><div class="lbl">Business Files</div></div>
<div class="stat"><div class="num">{s['total_size_mb']}</div><div class="lbl">Size (MB)</div></div>
<div class="stat"><div class="num">{s['vendor_js_files']}</div><div class="lbl">Vendor JS Waste</div></div>
<div class="stat"><div class="num">{s['vendor_js_waste_mb']}</div><div class="lbl">Vendor Waste (MB)</div></div>
<div class="stat{' danger' if s['duplicate_excess_files'] > 50 else ' warn' if s['duplicate_excess_files'] > 10 else ' ok'}"><div class="num">{s['duplicate_excess_files']}</div><div class="lbl">Duplicate Excess Files</div></div>
<div class="stat"><div class="num">{s['duplicate_waste_mb']}</div><div class="lbl">Duplicate Waste (MB)</div></div>
</div>
""")
    # By type
    f.write('<div class="card"><h2>File Types</h2><table><tr><th>Category</th><th>Count</th><th>%</th></tr>')
    total = s["total_files"]
    for t, cnt in sorted(report["by_type"].items(), key=lambda x: -x[1]):
        pct = round(cnt / total * 100, 1) if total else 0
        f.write(f"<tr><td>{t}</td><td>{cnt}</td><td>{pct}%</td></tr>")
    f.write("</table></div>")

    # Duplicates
    dups = report.get("duplicates", {})
    if dups:
        f.write(f'<div class="card dedup"><h2>🔁 Duplicate Groups ({len(dups)})</h2><table><tr><th>Files</th><th>Paths</th></tr>')
        for md5, paths in sorted(dups.items(), key=lambda x: -len(x[1]))[:50]:
            f.write(f"<tr><td>{len(paths)}</td><td>{'<br>'.join(paths[:5])}" + ('<br>...' if len(paths) > 5 else '') + "</td></tr>")
        f.write("</table></div>")
    else:
        f.write('<div class="card ok"><h2>✅ No duplicates found</h2></div>')

    f.write("</body></html>")


if __name__ == "__main__":
    scan()
