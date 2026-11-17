"""Serveur local de développement : sans cache, avec rechargement automatique.

Usage : python tools/serve.py [port]   (5520 par défaut) puis http://localhost:5520

Dès qu'un fichier du site change (HTML, CSS, JS, images), la page ouverte se recharge seule.
Le petit script de rechargement n'est ajouté qu'ici, à l'envoi : il n'est jamais dans les fichiers
du site et ne part donc jamais en production.
"""
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATCHED = ("*.html", "*.css", "*.js", "*.png", "*.svg", "*.ico", "*.webmanifest", "*.xml", "*.txt", "*.pdf", "*.webp", "en/*.html")

LIVE_RELOAD = """<script>
(() => {  // rechargement automatique (serveur local uniquement)
  let last = null;
  setInterval(async () => {
    try {
      const v = await (await fetch('/__livereload', { cache: 'no-store' })).text();
      if (last !== null && v !== last) location.reload();
      last = v;
    } catch (e) { /* serveur arrêté ou en cours de redémarrage */ }
  }, 800);
})();
</script>
""".encode("utf-8")


def site_version() -> str:
    """Empreinte des fichiers du site : change dès qu'un fichier est modifié, ajouté ou supprimé."""
    files = sorted(p for pattern in WATCHED for p in ROOT.glob(pattern))
    return "|".join(f"{p.name}:{p.stat().st_mtime_ns}" for p in files)


class DevHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/__livereload":
            return self._send(site_version().encode(), "text/plain; charset=utf-8")
        file = Path(self.translate_path(path))
        if file.is_dir():
            file = file / "index.html"
        if file.suffix == ".html" and file.is_file():
            html = file.read_bytes()
            html = html.replace(b"</body>", LIVE_RELOAD + b"</body>", 1)
            return self._send(html, "text/html; charset=utf-8")
        return super().do_GET()

    def _send(self, body: bytes, content_type: str):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # pas de ligne de journal toutes les 800 ms
        if "/__livereload" not in (args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5520
    handler = partial(DevHandler, directory=str(ROOT))
    print(f"http://localhost:{port}  (sans cache, rechargement automatique, Ctrl+C pour arrêter)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
