"""Vérifications du site avant mise en ligne (lancées par GitHub Actions, et en local).

Usage : python tools/check-site.py
"""
import json, re, sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Même liste que deploy/portfolio-sync.sh : ce sont les seuls fichiers publiés.
SITE_FILES = [
    "index.html", "styles.css", "main.js", "404.html",
    "og-image.png", "favicon.ico", "favicon.svg", "apple-touch-icon.png", "icon-192.png", "icon-512.png",
    "site.webmanifest", "robots.txt", "sitemap.xml",
]
errors = []

def check(ok, msg):
    if not ok:
        errors.append(msg)

# Fichiers présents, sans lien symbolique
for name in SITE_FILES + ["deploy/nginx.conf"]:
    p = ROOT / name
    check(p.exists(), f"fichier manquant : {name}")
    check(not p.is_symlink(), f"lien symbolique refusé : {name}")

html = (ROOT / "index.html").read_text(encoding="utf-8")

# Référencement
title = re.search(r"<title>(.*?)</title>", html, re.S)
check(title and len(title.group(1)) <= 60, "titre absent ou de plus de 60 caractères")
desc = re.search(r'<meta name="description" content="([^"]*)"', html)
check(desc and 50 <= len(desc.group(1)) <= 160, "description absente ou hors de 50 à 160 caractères")
canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
check(canonical, "balise canonical absente")
check(html.count("<h1") == 1, "la page doit avoir exactement un h1")

# Données structurées, manifeste, sitemap
for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
    try:
        json.loads(block)
    except json.JSONDecodeError as e:
        errors.append(f"données structurées invalides : {e}")
try:
    json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
except json.JSONDecodeError as e:
    errors.append(f"site.webmanifest invalide : {e}")
try:
    tree = ElementTree.parse(ROOT / "sitemap.xml")
    locs = [e.text for e in tree.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    if canonical:
        check(canonical.group(1) in locs, "l'adresse canonical n'est pas dans sitemap.xml")
except ElementTree.ParseError as e:
    errors.append(f"sitemap.xml invalide : {e}")
if canonical:
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    check(f"Sitemap: {canonical.group(1)}sitemap.xml" in robots, "robots.txt ne pointe pas vers le bon sitemap")

# Politique de sécurité : aucun script inline exécutable (seul le JSON-LD est autorisé)
for attrs in re.findall(r"<script([^>]*)>", html):
    check("application/ld+json" in attrs or "src=" in attrs, "script inline interdit par la CSP : le mettre dans main.js")
check(not re.search(r"\son[a-z]+=\"", html), "attribut onclick/onload… interdit par la CSP")

# Le numéro de téléphone ne doit jamais apparaître en clair
phone = re.compile(r"(?:\+33\s?|0)[67](?:[\s.-]?\d{2}){4}")
for name in SITE_FILES:
    p = ROOT / name
    if p.suffix in {".html", ".js", ".css", ".xml", ".txt", ".webmanifest"} and p.exists():
        check(not phone.search(p.read_text(encoding="utf-8")), f"numéro de téléphone en clair dans {name}")

if errors:
    print("Échec :")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print(f"OK : {len(SITE_FILES)} fichiers, référencement, données structurées et sécurité vérifiés")
