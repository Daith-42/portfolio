# Mise en ligne automatique du portfolio

Adresse : **https://david-ameline.daith42.fr/** (`daith42.fr` et `www.daith42.fr` y redirigent).

## Comment ça marche

```
 PC ── git push ──► GitHub : branche main ──► vérification automatique (GitHub Actions)
                                │
                     git push origin main:prod   (refusé si la vérification n'est pas verte)
                                ▼
                    GitHub : branche prod
                                ▲
                                │ toutes les 2 min, le SERVEUR regarde la branche (lecture seule)
 asushome1 ── portfolio-sync.timer ── portfolio-sync.sh ──► ~/stacks/portfolio/site + nginx/
                                                              │
                     conteneur « portfolio » (nginx) ◄────────┘  ◄── tunnel asushome1 ◄── visiteurs
```

- **`main`** : ta branche de travail. **`prod`** : ce qui est en ligne.
- **Le serveur va chercher** la branche `prod` : rien n'entre sur ton réseau, et GitHub n'a aucun
  accès au serveur ni aucun secret. Le dépôt est public, donc aucun identifiant n'est nécessaire.
- **Seuls les 13 fichiers du site et `deploy/nginx.conf` viennent du dépôt.** `compose.yaml`, le
  script de synchro et les unités systemd sont installés à la main et ne sont jamais modifiés
  automatiquement. Même si ton compte GitHub était piraté, on ne pourrait changer que le contenu
  du site, jamais prendre la main sur le serveur.
- Le script refuse les liens symboliques (qui pourraient publier un fichier privé du serveur) et
  vérifie la config nginx avant de l'appliquer : en cas de problème, **l'ancien site reste en
  ligne**.

Testé le 7 novembre 2026 dans un bac à sable Docker : premier déploiement, mise à jour du contenu,
changement de config nginx, lien symbolique malveillant refusé, config invalide refusée,
redirections et 404.

---

## Installation (une seule fois)

### 1. Envoyer les fichiers sur GitHub

Sur le PC, à la racine du dossier `portfolio` :

```bash
git add -A
```

```bash
git status
```

Tu dois voir : `.github/workflows/verifier.yml`, `tools/check-site.py`, les trois fichiers
`deploy/portfolio-sync.*`, `deploy/compose.yaml` et `deploy/nginx.conf` modifiés, et
`deploy/Dockerfile`, `deploy/.env.example`, `tools/deploy.sh` supprimés.

```bash
git commit -m "Déploiement automatique depuis la branche prod"
```

```bash
git push
```

Sur https://github.com/Daith-42/portfolio/actions, la vérification **Vérification** se lance.
Attends qu'elle soit verte (environ une minute), puis crée la branche `prod` :

```bash
git push origin main:prod
```

### 2. Protéger la branche prod sur GitHub

https://github.com/Daith-42/portfolio/settings/rules → **New ruleset** → **New branch ruleset** :

- **Ruleset name** : `prod`
- **Enforcement status** : **Active**
- **Target branches** → **Add target** → **Include by pattern** → `prod`
- Coche **Restrict deletions** et **Block force pushes**
- Coche **Require status checks to pass** → **Add checks** → tape `verifier` et sélectionne-le
- **Create**

Désormais, `git push origin main:prod` est refusé tant que la vérification de ce commit n'est pas
verte.

### 3. Ajouter l'adresse dans Cloudflare

Zero Trust → **Networks** → **Tunnels** → `asushome1` → **Routes** → **Add route** →
**Published application** :

- **Subdomain** : `david-ameline`
- **Domain** : `daith42.fr`
- **Service URL** : `http://portfolio:8080`

Garde les routes `daith42.fr` et `www.daith42.fr` : elles redirigent maintenant vers
`david-ameline.daith42.fr`.

### 4. Installer la synchro sur le serveur

```bash
ssh daith@asushome1
```

Sur le serveur, récupère la branche `prod` :

```bash
cd ~/stacks/portfolio && git clone --quiet --depth 1 --branch prod --single-branch https://github.com/Daith-42/portfolio.git repo
```

**Lis le script avant de l'installer** : c'est lui qui tournera toutes les 2 minutes.

```bash
less repo/deploy/portfolio-sync.sh
```

Installe la config fixe et le script (ils remplacent l'ancien `compose.yaml`) :

```bash
cp repo/deploy/compose.yaml compose.yaml && cp repo/deploy/portfolio-sync.sh portfolio-sync.sh && chmod 700 portfolio-sync.sh
```

Premier déploiement : remplit `site/` (la page « en construction » disparaît) et `nginx/` :

```bash
./portfolio-sync.sh
```

Redémarre le conteneur avec la nouvelle config :

```bash
docker compose up -d && docker compose ps
```

`portfolio` doit être **Up** puis **(healthy)** au bout d'une trentaine de secondes.

Vérifie depuis le réseau `web` :

```bash
docker run --rm --network web alpine wget -qS -O /dev/null --header "Host: david-ameline.daith42.fr" http://portfolio:8080/ 2>&1 | head -3
```

### 5. Lancer la synchro toutes les 2 minutes

```bash
sudo cp repo/deploy/portfolio-sync.service repo/deploy/portfolio-sync.timer /etc/systemd/system/
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now portfolio-sync.timer
```

Vérifie :

```bash
systemctl list-timers portfolio-sync.timer
```

```bash
sudo systemctl start portfolio-sync.service && journalctl -u portfolio-sync -n 20 --no-pager
```

La dernière commande ne doit afficher aucune ligne « ÉCHEC ».

### 6. Être prévenu si une mise à jour échoue (Uptime Kuma)

1. http://asushome1:3001 → **Add New Monitor** → type **Push**, nom `Portfolio – synchro`,
   **Heartbeat Interval** : `300` secondes → **Save**.
2. Copie l'adresse **Push URL** affichée, **sans** la partie qui commence par `?`
   (elle finit par le jeton). Remplace `asushome1` par `100.74.216.35` si besoin.
3. Sur le serveur :

   ```bash
   nano ~/stacks/portfolio/sync.env
   ```

   Une ligne : `PUSH_URL=http://100.74.216.35:3001/api/push/LE-JETON`, puis Ctrl+O, Entrée,
   Ctrl+X.

   ```bash
   chmod 600 ~/stacks/portfolio/sync.env
   ```

4. Ajoute aussi un moniteur **HTTP(s)** vers `https://david-ameline.daith42.fr/`.

À chaque passage (toutes les 2 min), le script envoie « up » ; en cas d'échec, « down » avec la
raison. S'il ne donne plus de nouvelles pendant 5 minutes, Uptime Kuma te prévient aussi.

### 7. Vérifications finales

- https://david-ameline.daith42.fr/ sur ton téléphone **en 4G** : menu, « Afficher le numéro »,
  liens des projets.
- https://daith42.fr/ redirige vers https://david-ameline.daith42.fr/.
- https://securityheaders.com/?q=david-ameline.daith42.fr : note A ou A+.
- https://www.linkedin.com/post-inspector/ : l'image et le titre apparaissent.
- Google Search Console : ajoute la propriété **Domaine** `daith42.fr` (enregistrement TXT dans
  Cloudflare, sans toucher aux MX, SPF ni DMARC), puis **Sitemaps** →
  `https://david-ameline.daith42.fr/sitemap.xml`.

---

## Au quotidien : mettre à jour le site

```bash
git add -A
```

```bash
git commit -m "Ce qui change"
```

```bash
git push
```

Attends la coche verte sur GitHub (onglet **Actions**), puis :

```bash
git push origin main:prod
```

Le site est à jour **en 2 minutes au plus**. Pour le voir passer sur le serveur :

```bash
journalctl -u portfolio-sync -f
```

**Revenir en arrière** : annule le commit fautif sur `main`, puis renvoie sur `prod`.

```bash
git revert HEAD
```

```bash
git push && git push origin main:prod
```

**Vérifier en local avant d'envoyer** :

```bash
python tools/check-site.py
```

## Ce qui ne se met PAS à jour tout seul

Volontairement, pour la sécurité. Si tu modifies l'un de ces fichiers dans le dépôt, il faut le
réinstaller à la main sur le serveur, après l'avoir relu :

| Fichier | Réinstallation (sur le serveur, dans `~/stacks/portfolio`) |
|---|---|
| `deploy/compose.yaml` | `cp repo/deploy/compose.yaml . && docker compose up -d` |
| `deploy/portfolio-sync.sh` | `cp repo/deploy/portfolio-sync.sh . && chmod 700 portfolio-sync.sh` |
| `deploy/portfolio-sync.service` / `.timer` | `sudo cp repo/deploy/portfolio-sync.{service,timer} /etc/systemd/system/ && sudo systemctl daemon-reload` |

(`repo/` est mis à jour par la synchro à chaque nouveau commit sur `prod`.)

**Mettre à jour nginx** : change le tag `nginxinc/nginx-unprivileged:1.30-alpine` aux trois
endroits (`deploy/compose.yaml`, `deploy/portfolio-sync.sh`, `.github/workflows/verifier.yml`),
envoie sur `prod`, puis réinstalle `compose.yaml` et le script comme ci-dessus.

## Dépannage

| Symptôme | Où regarder |
|---|---|
| La vérification GitHub est rouge | Onglet **Actions** → le commit → l'étape en rouge dit quoi corriger |
| Le site ne se met pas à jour | `journalctl -u portfolio-sync -n 50 --no-pager` sur le serveur |
| « lien symbolique refusé » | Un fichier du site est un lien : remplace-le par un vrai fichier |
| « config nginx invalide » | Corrige `deploy/nginx.conf` ; l'ancien site reste en ligne en attendant |
| Forcer un redéploiement | `~/stacks/portfolio/portfolio-sync.sh --force` |
| Arrêter les mises à jour | `sudo systemctl disable --now portfolio-sync.timer` |

## À ajouter dans la fiche du serveur

Dans `asus_serv/asushome1-agent.md`, section **Outils installés** :

`| portfolio-sync (timer systemd) | Met à jour le portfolio depuis la branche prod du dépôt public, toutes les 2 min | journalctl -u portfolio-sync |`
