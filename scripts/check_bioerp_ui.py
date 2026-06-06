import re

html = open(r"D:\ERP System\BIO_ERP\app\organs\incentivehouse_organ\templates\main_dashboard.html", encoding="utf-8").read()

print("BIO-ERP old system UI elements:")
checks = [
    ("header bar", "class=\"header\"" in html or "header" in html.lower()),
    ("footer status bar", "status-bar" in html or "status_bar" in html),
    ("logout button", "logout" in html.lower()),
    ("search input", "search" in html.lower() and "input" in html),
    ("user display", "header-user" in html or "user" in html.lower()),
    ("nav sidebar", "sidebar" in html.lower()),
    ("module cards", "module-card" in html or "module_grid" in html),
    ("breadcrumb", "breadcrumb" in html.lower()),
    ("gold color theme", "#D4A017" in html),
]
for label, found in checks:
    print(f"  {'PASS' if found else 'FAIL'}: {label}")

images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
print(f"\nImages: {images}")
