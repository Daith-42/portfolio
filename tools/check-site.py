"""Vérifications du site avant mise en ligne (lancées par GitHub Actions, et en local).

Usage : py tools/check-site.py
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Même liste que deploy/portfolio-sync.sh : ce sont les seuls fichiers publiés.
SITE_FILES = [
    "index.html", "en/index.html", "styles.css", "main.js", "404.html",
    "og-image.png", "og-image-en.png", "favicon.ico", "favicon.svg", "apple-touch-icon.png", "icon-192.png", "icon-512.png",
    "site.webmanifest", "robots.txt", "sitemap.xml",
    "cv-david-ameline.pdf", "cv-apercu.webp",
]
# Pages indexées : (fichier, langue attendue)
PAGES = [("index.html", "fr"), ("en/index.html", "en")]
ASSETS = ["styles.css", "main.js", "cv-david-ameline.pdf", "cv-apercu.webp"]
errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


# Fichiers présents, sans lien symbolique
for name in SITE_FILES + ["deploy/nginx.conf"]:
    p = ROOT / name
    check(p.exists(), f"fichier manquant : {name}")
    check(not p.is_symlink(), f"lien symbolique refusé : {name}")

# La page anglaise est générée depuis la française : elle doit être à jour et complète
gen = subprocess.run([sys.executable, str(ROOT / "tools" / "build-en.py"), "--check"], capture_output=True, text=True, encoding="utf-8")
check(gen.returncode == 0, "page anglaise : " + (gen.stdout.strip() or gen.stderr.strip()).replace("\n", " / "))

# Sitemap
try:
    tree = ElementTree.parse(ROOT / "sitemap.xml")
    locs = [e.text for e in tree.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
except ElementTree.ParseError as e:
    locs = []
    errors.append(f"sitemap.xml invalide : {e}")

alternates = {}
for page, lang in PAGES:
    path = ROOT / page
    if not path.exists():
        continue
    html = path.read_text(encoding="utf-8")

    # Langue et référencement
    check(f'<html lang="{lang}">' in html, f"{page} : <html lang=\"{lang}\"> attendu")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    check(title and len(title.group(1)) <= 60, f"{page} : titre absent ou de plus de 60 caractères")
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    check(desc and 50 <= len(desc.group(1)) <= 160, f"{page} : description absente ou hors de 50 à 160 caractères")
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    check(canonical, f"{page} : balise canonical absente")
    check(html.count("<h1") == 1, f"{page} : la page doit avoir exactement un h1")
    if canonical:
        check(canonical.group(1) in locs, f"{page} : l'adresse canonical n'est pas dans sitemap.xml")
    alternates[page] = (canonical.group(1) if canonical else None, lang,
                        dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', html)))

    # Données structurées
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(block)
        except json.JSONDecodeError as e:
            errors.append(f"{page} : données structurées invalides : {e}")

    # Politique de sécurité : aucun script inline exécutable (seul le JSON-LD est autorisé)
    for attrs in re.findall(r"<script([^>]*)>", html):
        check("application/ld+json" in attrs or "src=" in attrs, f"{page} : script inline interdit par la CSP, le mettre dans main.js")
    check(not re.search(r"\son[a-z]+=\"", html), f"{page} : attribut onclick/onload… interdit par la CSP")

# hreflang : chaque page annonce toutes les langues, et chaque langue pointe vers sa page canonique
for page, (canon, lang, alts) in alternates.items():
    check(alts.get(lang) == canon, f"{page} : hreflang=\"{lang}\" doit pointer vers sa propre adresse")
    for other, (other_canon, other_lang, _) in alternates.items():
        check(alts.get(other_lang) == other_canon, f"{page} : hreflang=\"{other_lang}\" manquant ou faux")
    check("x-default" in alts, f"{page} : hreflang=\"x-default\" manquant")

robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
fr_canon = alternates.get("index.html", (None,))[0]
if fr_canon:
    check(f"Sitemap: {fr_canon}sitemap.xml" in robots, "robots.txt ne pointe pas vers le bon sitemap")

try:
    json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
except json.JSONDecodeError as e:
    errors.append(f"site.webmanifest invalide : {e}")

# Empreintes CSS/JS/CV à jour (sinon les visiteurs gardent d'anciennes copies en cache)
for page in ["index.html", "en/index.html", "404.html"]:
    path = ROOT / page
    if not path.exists():
        continue
    page_html = path.read_text(encoding="utf-8")
    for asset in ASSETS:
        if not (ROOT / asset).exists() or not re.search(r'(?:href|src)="/?' + re.escape(asset), page_html):
            continue
        expected = hashlib.sha256((ROOT / asset).read_bytes()).hexdigest()[:8]
        found = re.findall(r'(?:href|src)="/?' + re.escape(asset) + r'(?:\?v=([0-9a-f]+))?"', page_html)
        check(found and all(v == expected for v in found),
              f"{page} : empreinte de {asset} pas à jour, lance py tools/version-assets.py puis py tools/build-en.py")

# Le numéro de téléphone ne doit jamais apparaître en clair
# Pas au milieu d'un autre nombre (les tracés SVG contiennent de longues suites de décimales).
phone = re.compile(r"(?<![\d.])(?:\+33\s?|0)[67](?:[\s.-]?\d{2}){4}(?![\d])")
for name in SITE_FILES:
    p = ROOT / name
    if p.suffix in {".html", ".js", ".css", ".xml", ".txt", ".webmanifest"} and p.exists():
        check(not phone.search(p.read_text(encoding="utf-8")), f"numéro de téléphone en clair dans {name}")

# Le CV en ligne ne doit pas contenir de numéro de téléphone (un PDF est lu et indexé par les robots).
# Choix assumé le 17/11/2026 : le CV actuel part avec le numéro, en attendant une version sans.
# Remettre à False dès que le CV sans numéro est en place (py tools/build-cv.py).
CV_PHONE_ALLOWED = True

cv = ROOT / "cv-david-ameline.pdf"
if cv.exists() and not CV_PHONE_ALLOWED:
    try:
        from pypdf import PdfReader
        cv_text = " ".join(page.extract_text() or "" for page in PdfReader(str(cv)).pages)
        check(not phone.search(cv_text), "numéro de téléphone dans cv-david-ameline.pdf : exporte le CV sans le numéro, puis py tools/build-cv.py")
    except ImportError:
        errors.append("pypdf manquant pour vérifier le CV : py -m pip install --user pypdf")

if errors:
    print("Échec :")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print(f"OK : {len(SITE_FILES)} fichiers, 2 langues, référencement, données structurées et sécurité vérifiés")
