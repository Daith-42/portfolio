"""Rend tools/og-image.html en og-image.png (1200×630) avec Chrome ou Edge en mode headless.

Usage : python tools/build-og.py
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "og-image.html"
OUT = ROOT / "og-image.png"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]
browser = next((c for c in CANDIDATES if c and os.path.exists(c)), None)
if not browser:
    sys.exit("Chrome ou Edge introuvable.")

with tempfile.TemporaryDirectory() as profile:
    subprocess.run([
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--user-data-dir={profile}", "--force-device-scale-factor=1",
        "--window-size=1200,630", "--virtual-time-budget=8000",
        f"--screenshot={OUT}", SRC.as_uri(),
    ], check=True, capture_output=True, timeout=60)

print(f"OK : {OUT}")
