import re, sys

html = open(sys.argv[1]).read()

print("=== RENDERED HTML ANALYSIS ===")
print(f"HTML size: {len(html)} bytes")

checks = {
    "  header tag (<header>)": "<header" in html.lower(),
    "  logo img (ihe_logo.png)": "ihe_logo.png" in html,
    "  footer tag (<footer>)": "<footer" in html.lower(),
    "  copyright": "2026" in html,
    "  sidebar nav (/evn link)": "/evn" in html,
    "  AI orb widget": "ai-orb" in html,
    "  top navigation bar": bool(re.search(r'top.?bar|navbar|header-bar|topbar', html, re.I)),
    "  user name / logout": bool(re.search(r'user|logout|sign.?out', html, re.I)),
    "  status bar (bottom)": bool(re.search(r'status.?bar|connection|sql.?server|db.?status', html, re.I)),
    "  global search input": 'search' in html.lower() and '<input' in html,
    "  breadcrumb navigation": 'breadcrumb' in html.lower(),
    "  big hero/header image": 'logos.jpg' in html,
}

print("\nChecks:")
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}: {k}")

images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
print(f"\nImages in rendered HTML: {images}")
print(f"Total <img> tags: {len(images)}")

# Check for critical missing UI elements
print("\n=== CRITICAL GAPS ===")
if not checks["  header tag (<header>)"] and not checks["  top navigation bar"]:
    print("  [MISSING] No header/top bar at all")
if not checks["  footer tag (<footer>)"]:
    print("  [MISSING] No <footer> tag in main content")
if not checks["  status bar (bottom)"]:
    print("  [MISSING] No status bar (DB health, connection)")
if not checks["  user name / logout"]:
    print("  [MISSING] No user session UI")
if not checks["  global search input"]:
    print("  [MISSING] No global search")
