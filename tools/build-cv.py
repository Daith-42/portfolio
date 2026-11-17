"""Prépare le CV du site : copie le PDF sous un nom propre et génère son aperçu en image.

Usage : py tools/build-cv.py "chemin/vers/mon CV.pdf"
Produit, à la racine du site :
  - cv-david-ameline.pdf   le fichier téléchargé par les visiteurs
  - cv-apercu.webp         l'image de la 1re page, pour la miniature et la pop-up d'aperçu
Puis lance tools/version-assets.py pour mettre à jour les empreintes.

Dépendance : pypdfium2 (py -m pip install --user pypdfium2), Pillow.
Rappel : tools/check-site.py refuse la mise en ligne si le PDF contient un numéro de téléphone.
"""
import shutil, subprocess, sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parent.parent
PDF_OUT = ROOT / "cv-david-ameline.pdf"
PREVIEW_OUT = ROOT / "cv-apercu.webp"
PREVIEW_WIDTH = 1100  # px : net dans la pop-up, léger à charger


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 2:
        sys.exit('Usage : py tools/build-cv.py "chemin/vers/mon CV.pdf"')
    src = Path(sys.argv[1])
    if not src.is_file() or src.suffix.lower() != ".pdf":
        sys.exit(f"Fichier PDF introuvable : {src}")

    shutil.copyfile(src, PDF_OUT)

    pdf = pdfium.PdfDocument(str(PDF_OUT))
    page = pdf[0]
    scale = PREVIEW_WIDTH / page.get_width()
    image = page.render(scale=scale).to_pil().convert("RGB")
    image.save(PREVIEW_OUT, "WEBP", quality=82, method=6)
    pdf.close()

    print(f"PDF   : {PDF_OUT.name} ({PDF_OUT.stat().st_size // 1024} Ko)")
    print(f"Aperçu : {PREVIEW_OUT.name} ({image.width}×{image.height}, {PREVIEW_OUT.stat().st_size // 1024} Ko)")
    subprocess.run([sys.executable, str(ROOT / "tools" / "version-assets.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build-en.py")], check=True)


if __name__ == "__main__":
    main()
