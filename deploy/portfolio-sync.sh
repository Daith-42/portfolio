#!/usr/bin/env bash
# Synchronisation automatique du portfolio sur asushome1.
#
# Lancé toutes les 2 minutes par portfolio-sync.timer (utilisateur daith).
# Regarde la branche prod du dépôt public ; s'il y a un nouveau commit :
#   1. copie UNIQUEMENT les fichiers de la liste ci-dessous (jamais de lien symbolique) ;
#   2. vérifie la config nginx avec l'image du site (nginx -t) avant de l'appliquer ;
#   3. remplace site/ et nginx/, puis recharge nginx sans coupure.
# compose.yaml et ce script ne viennent JAMAIS du dépôt : ils s'installent à la main.
#
# Lancement manuel :   ~/stacks/portfolio/portfolio-sync.sh
# Forcer un redéploiement :   ~/stacks/portfolio/portfolio-sync.sh --force
set -euo pipefail

REPO_URL="${PORTFOLIO_REPO_URL:-https://github.com/Daith-42/portfolio.git}"
BRANCH="prod"
STACK="$HOME/stacks/portfolio"
IMAGE="nginxinc/nginx-unprivileged:1.30-alpine"
CONTAINER="portfolio"

# Les seuls fichiers publiés.
SITE_FILES=(
  index.html styles.css main.js 404.html
  og-image.png favicon.ico favicon.svg apple-touch-icon.png icon-192.png icon-512.png
  site.webmanifest robots.txt sitemap.xml
)
NGINX_SRC="deploy/nginx.conf"

REPO="$STACK/repo"
STAGE="$STACK/.stage"
STATE="$STACK/.deployed"
# Facultatif : PUSH_URL=<adresse push Uptime Kuma> dans ce fichier (chmod 600).
SYNC_ENV="$STACK/sync.env"

log() { echo "[portfolio-sync] $*"; }

PUSH_URL=""
if [ -f "$SYNC_ENV" ]; then
  PUSH_URL="$(grep -E '^PUSH_URL=' "$SYNC_ENV" | head -1 | cut -d= -f2- || true)"
fi
notify() { # notify up|down "message"
  [ -n "$PUSH_URL" ] || return 0
  curl -fsS -m 10 -G "$PUSH_URL" --data-urlencode "status=$1" --data-urlencode "msg=$2" >/dev/null || true
}
fail() { log "ÉCHEC : $*"; notify down "$*"; exit 1; }
trap 'fail "erreur ligne $LINENO"' ERR

# Une seule synchro à la fois.
exec 9>"$STACK/.sync.lock"
flock -n 9 || { log "déjà en cours"; exit 0; }

# 1. Récupérer la branche prod (dépôt public : aucun identifiant).
if [ ! -d "$REPO/.git" ]; then
  log "premier clonage de $BRANCH"
  git clone --quiet --depth 1 --branch "$BRANCH" --single-branch "$REPO_URL" "$REPO"
fi
git -C "$REPO" fetch --quiet --depth 1 origin "$BRANCH"
NEW="$(git -C "$REPO" rev-parse FETCH_HEAD)"
CUR="$(cat "$STATE" 2>/dev/null || true)"

if [ "$NEW" = "$CUR" ] && [ "${1:-}" != "--force" ]; then
  notify up "à jour (${NEW:0:7})"
  exit 0
fi
log "nouveau commit ${NEW:0:7} (en ligne : ${CUR:0:7})"
git -C "$REPO" -c advice.detachedHead=false checkout --quiet --force "$NEW"
git -C "$REPO" clean --quiet -fdx

# 2. Préparer site/ et nginx/ dans un dossier à part, fichier par fichier.
rm -rf "$STAGE"
mkdir -p "$STAGE/site" "$STAGE/nginx"
copy_regular() { # copy_regular <source dans le dépôt> <destination>
  local src="$REPO/$1"
  [ -L "$src" ] && fail "$1 est un lien symbolique, refusé"
  [ -f "$src" ] || fail "$1 manquant dans $BRANCH"
  cp --no-dereference --preserve=timestamps "$src" "$2"
}
for f in "${SITE_FILES[@]}"; do
  copy_regular "$f" "$STAGE/site/$f"
done
copy_regular "$NGINX_SRC" "$STAGE/nginx/default.conf"
chmod -R a+rX,go-w "$STAGE"

# 3. Vérifier la config nginx avec la même image que le site, sans réseau.
docker run --rm --network none --read-only --tmpfs /tmp \
  -v "$STAGE/nginx:/etc/nginx/conf.d:ro" -v "$STAGE/site:/usr/share/nginx/html:ro" \
  "$IMAGE" nginx -t -q || fail "config nginx invalide dans ${NEW:0:7}"

# 4. Appliquer.
NGINX_CHANGED=1
if [ -f "$STACK/nginx/default.conf" ] && cmp -s "$STAGE/nginx/default.conf" "$STACK/nginx/default.conf"; then
  NGINX_CHANGED=0
fi
mkdir -p "$STACK/site" "$STACK/nginx"
rsync -a --delete "$STAGE/site/" "$STACK/site/"
rsync -a --delete "$STAGE/nginx/" "$STACK/nginx/"
rm -rf "$STAGE"

if [ "$NGINX_CHANGED" = 1 ] && docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  docker exec "$CONTAINER" nginx -s reload
  log "nginx rechargé"
fi

echo "$NEW" > "$STATE"
log "en ligne : ${NEW:0:7}"
notify up "déployé ${NEW:0:7}"
