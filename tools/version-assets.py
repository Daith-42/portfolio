"""Ajoute une empreinte aux fichiers CSS et JS dans les pages (styles.css?v=1a2b3c4d).

Dès qu'un fichier change, son adresse change : les navigateurs et Cloudflare ne peuvent plus
servir une ancienne copie gardée en cache avec une nouvelle page.

À lancer après chaque modification de styles.css ou main.js :
    python tools/version-assets.py
(tools/check-site.py refuse la mise en ligne si une empreinte n'est pas à jour.)
"""
import hashlib, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ["styles.css", "main.js", "cv-david-ameline.pdf", "cv-apercu.webp"]
PAGES = ["index.html", "404.html"]  # en/index.html est régénérée depuis index.html (tools/build-en.py)


def fingerprint(name: str) -> str:
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:8]


def pattern(name: str) -> re.Pattern:
    # href="styles.css", href="/styles.css" ou src="main.js?v=…", avec ou sans empreinte
    return re.compile(r'((?:href|src)="/?' + re.escape(name) + r')(?:\?v=[0-9a-f]+)?"')


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    assets = [a for a in ASSETS if (ROOT / a).exists()]
    for page in PAGES:
        path = ROOT / page
        text = path.read_text(encoding="utf-8")
        new = text
        for asset in assets:
            new = pattern(asset).sub(lambda m: f'{m.group(1)}?v={fingerprint(asset)}"', new)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            print(f"mis à jour : {page}")
    for asset in assets:
        print(f"{asset} → ?v={fingerprint(asset)}")


if __name__ == "__main__":
    main()
