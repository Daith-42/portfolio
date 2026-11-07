"""Remplace l'adresse du site partout où elle apparaît (canonical, Open Graph,
données structurées, robots.txt, sitemap, image de partage).

Usage : python tools/set-domain.py https://nouvelle-adresse.fr/
Puis régénérer l'image de partage : python tools/build-og.py
"""
import re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
FILES = ["index.html", "robots.txt", "sitemap.xml", "tools/og-image.html"]

if len(sys.argv) != 2 or not sys.argv[1].startswith("https://"):
    sys.exit("Usage : python tools/set-domain.py https://nouvelle-adresse.fr/")
new = sys.argv[1].rstrip("/") + "/"

html = (ROOT / "index.html").read_text(encoding="utf-8")
old = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
if old == new:
    sys.exit(f"Déjà à jour : {new}")

old_host, new_host = old.split("//", 1)[1].rstrip("/"), new.split("//", 1)[1].rstrip("/")
for name in FILES:
    p = ROOT / name
    text = p.read_text(encoding="utf-8")
    text = text.replace(old, new).replace(old_host, new_host)
    p.write_text(text, encoding="utf-8", newline="\n")
    print(f"mis à jour : {name}")
print(f"{old} → {new}")
