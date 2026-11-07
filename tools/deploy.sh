#!/usr/bin/env bash
# Met le portfolio en ligne sur asushome1 (par Tailscale + SSH).
#
#   bash tools/deploy.sh            envoie le site et reconstruit le conteneur
#   bash tools/deploy.sh --local    prépare seulement le paquet dans build/ (pour tester)
#
# Prérequis : Tailscale connecté avec le compte daith420@, clé SSH du PC acceptée par le serveur,
# et la première installation faite (voir DEPLOIEMENT.md).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${DEPLOY_HOST:-daith@asushome1}"
REMOTE_DIR="stacks/portfolio"

# Les seuls fichiers publiés. Rien d'autre (versions/, tools/, .claude/) ne part sur le serveur.
SITE_FILES=(
  index.html styles.css main.js 404.html
  og-image.png favicon.ico favicon.svg apple-touch-icon.png icon-192.png icon-512.png
  site.webmanifest robots.txt sitemap.xml
)

BUILD="$ROOT/build"
rm -rf "$BUILD"
mkdir -p "$BUILD/site"
for f in "${SITE_FILES[@]}"; do
  [ -f "$ROOT/$f" ] || { echo "Fichier manquant : $f" >&2; exit 1; }
  cp "$ROOT/$f" "$BUILD/site/"
done
cp "$ROOT/deploy/Dockerfile" "$ROOT/deploy/nginx.conf" "$ROOT/deploy/compose.yaml" "$ROOT/deploy/.env.example" "$BUILD/"
echo "Paquet prêt : $BUILD ($(ls "$BUILD/site" | wc -l) fichiers dans site/)"

if [ "${1:-}" = "--local" ]; then
  exit 0
fi

echo "Envoi vers $HOST:~/$REMOTE_DIR …"
# Le .env du serveur (jeton du tunnel) n'est jamais écrasé : il n'est pas dans le paquet.
tar -C "$BUILD" -cf - . | ssh "$HOST" "set -e
  mkdir -p ~/$REMOTE_DIR
  rm -rf ~/$REMOTE_DIR/site
  tar -xf - -C ~/$REMOTE_DIR
  cd ~/$REMOTE_DIR
  if [ ! -f .env ]; then
    echo 'Pas de .env sur le serveur : fais d abord la première installation (DEPLOIEMENT.md, étape 3).' >&2
    exit 1
  fi
  docker compose config -q
  docker compose up -d --build
  docker image prune -f >/dev/null
  docker compose ps"

echo "En ligne. Vérifie : https://david-ameline.daith42.fr/"
