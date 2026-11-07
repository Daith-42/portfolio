# Mise en ligne du portfolio sur asushome1

> Site statique servi par nginx (sans droits root, conteneur en lecture seule), rendu public par
> **son propre Cloudflare Tunnel** : aucun port ouvert sur internet ni sur le réseau local, HTTPS
> et cache fournis par Cloudflare. Même principe que Zelda Collection, dans une stack séparée.
> Testé en local le 7 novembre 2026 : image construite, en-têtes de sécurité, 404, compression,
> fichiers non publiés bien refusés.

Adresse : **https://david-ameline.daith42.fr/**

Les commandes `bash` se lancent depuis Git Bash sur le PC Windows, à la racine du dossier
`portfolio`. Celles qui commencent par `ssh` ou qui sont marquées « sur le serveur » se lancent
sur `asushome1` (invite `daith@asushome1:~$`).

## 1. Ce qu'il te faut

- **Tailscale connecté** sur le PC, avec le compte `daith420@`, et `ssh daith@asushome1` qui
  fonctionne.
- Le domaine **`daith42.fr` géré par Cloudflare** (onglet **DNS** du domaine visible dans le
  tableau de bord Cloudflare). Sinon : **Add a domain**, puis remplace les « nameservers » chez
  ton registrar par ceux que Cloudflare affiche, et attends qu'il passe à **Active**.
- Le compte **Cloudflare Zero Trust** déjà ouvert (fait pour Zelda Collection ; sinon, voir le
  guide de Zelda Collection, étape 5.1).

## 2. Créer le tunnel « portfolio »

Un tunnel à part, pour que le portfolio et Zelda Collection restent indépendants.

1. https://one.dash.cloudflare.com → **Networks** → **Tunnels** → **Create a tunnel**.
2. **Cloudflared** → **Next**.
3. Nom : `portfolio` → **Save tunnel**.
4. À l'écran « Install and run a connector », choisis **Docker**. Dans la commande affichée,
   copie seulement la longue suite de caractères après `--token`. Garde la page ouverte.

## 3. Première installation sur le serveur

1. Prépare le dossier et le fichier du jeton :

   ```bash
   ssh daith@asushome1
   ```

   Puis, sur le serveur :

   ```bash
   mkdir -p ~/stacks/portfolio && cd ~/stacks/portfolio && nano .env
   ```

2. Dans l'éditeur, écris une seule ligne, en collant le jeton copié à l'étape 2 :

   ```
   TUNNEL_TOKEN=le-jeton-copié
   ```

   Enregistre avec **Ctrl+O**, **Entrée**, puis quitte avec **Ctrl+X**.

3. Protège le fichier, puis reviens sur le PC :

   ```bash
   chmod 600 .env && exit
   ```

Le jeton ne vit que dans ce `.env` sur le serveur. Ne l'envoie à personne, et pas dans le chat.

## 4. Envoyer le site

Sur le PC, à la racine du dossier `portfolio` :

```bash
bash tools/deploy.sh
```

Le script envoie seulement les 13 fichiers du site et la configuration du serveur (jamais
`versions/`, `tools/` ni le `.env`), construit l'image et démarre les deux conteneurs. Il affiche
à la fin `portfolio-web` et `portfolio-tunnel` en **Up**.

Vérifie depuis le PC (Tailscale connecté) : http://asushome1:3090. Le site n'est pas encore
public.

## 5. Ouvrir le site sur internet

De retour sur la page Cloudflare du tunnel : le connecteur est passé à **Connected**. Clique
**Next**, puis onglet **Public Hostname** :

- **Subdomain** : `david-ameline`
- **Domain** : `daith42.fr`
- **Service** : type **HTTP**, URL `web:8080`

**Save tunnel**. Cloudflare crée l'enregistrement DNS tout seul. Ouvre
https://david-ameline.daith42.fr/ : c'est en ligne.

Dans le tableau de bord du domaine `daith42.fr` → **SSL/TLS** → **Edge Certificates**, vérifie que
**Always Use HTTPS** est activé.

## 6. Vérifications

- Ouvre le site **sur ton téléphone**, en 4G/5G (pas en Wi-Fi maison) : menu, bouton
  « Afficher le numéro », liens des projets.
- Une adresse inventée, par exemple https://david-ameline.daith42.fr/test, affiche la page
  « Page introuvable ».
- **Aperçu de partage** : colle l'adresse sur https://www.linkedin.com/post-inspector/ ; l'image
  et le titre doivent apparaître.
- **En-têtes de sécurité** : https://securityheaders.com/?q=david-ameline.daith42.fr (note
  attendue : A ou A+).
- **Uptime Kuma** (http://asushome1:3001) → **Add New Monitor** → type **HTTP(s)**, URL
  `http://100.74.216.35:3090`, nom `Portfolio`. Ajoute aussi une sonde vers
  `https://david-ameline.daith42.fr/` pour surveiller le chemin complet par Cloudflare.
- Après le prochain redémarrage du serveur, `docker ps` doit montrer les deux conteneurs
  relancés seuls.

## 7. Google

1. https://search.google.com/search-console → **Ajouter une propriété** → **Domaine** →
   `daith42.fr`. Google donne un enregistrement **TXT** : ajoute-le dans Cloudflare (**DNS** →
   **Records** → **Add record**, type TXT, nom `@`), puis **Valider**.
2. Dans la propriété → **Sitemaps** → `https://david-ameline.daith42.fr/sitemap.xml` →
   **Envoyer**.
3. **Inspection de l'URL** → l'adresse du site → **Demander l'indexation**.

Compte quelques jours avant que le site apparaisse dans les résultats pour « David Ameline ».

## 8. Mettre à jour le site

Après une modification sur le PC :

```bash
bash tools/deploy.sh
```

Le site est remplacé en quelques secondes. Si tu as modifié le contenu, change aussi la date
`<lastmod>` de `sitemap.xml` et `dateModified` dans `index.html`.

Pour vérifier le paquet sans rien envoyer :

```bash
bash tools/deploy.sh --local
```

## 9. Arrêter ou retirer le site

Sur le serveur :

```bash
cd ~/stacks/portfolio && docker compose down
```

Puis supprime le tunnel `portfolio` dans Cloudflare (**Networks** → **Tunnels**). Il n'y a aucune
donnée à sauvegarder : tout le site est dans ce dossier `portfolio` sur le PC.

## Sécurité, en bref

- Aucun port ouvert sur internet ni sur le réseau local : le tunnel est une connexion sortante.
  Le port 3090 n'écoute que sur l'IP Tailscale `100.74.216.35`, pour les vérifications.
- Le tunnel ne joint que le conteneur `web`, sur un réseau Docker propre au portfolio : il ne
  voit ni Zelda Collection ni la stack d'administration.
- Le conteneur tourne sans droits root, en lecture seule, sans aucune capacité Linux, limité à
  64 Mo de mémoire.
- En-têtes envoyés sur chaque page : politique de contenu stricte (aucun script extérieur ni
  injecté), HTTPS seul, pas d'affichage dans le cadre d'un autre site, pas de caméra, micro ni
  géolocalisation.
- Seuls les fichiers du site sont servis : `.env`, `versions/`, `tools/` et les fichiers cachés
  répondent 404.

## À ajouter dans la fiche du serveur

Dans `asus_serv/asushome1-serv-spec.md`, pour garder la fiche à jour :

- tableau **Ports déjà utilisés** :
  `| 3090 | Portfolio, le site (vérification et Uptime Kuma) | 100.74.216.35 |`
- section **Exceptions validées** :

  > ### Portfolio — `~/stacks/portfolio`
  >
  > Site statique public (nginx sans droits root, lecture seule). **Public par son propre
  > Cloudflare Tunnel** (conteneur `portfolio-tunnel`, tunnel `portfolio`), sur un réseau Docker
  > propre à la stack. Port 3090 sur l'IP Tailscale seulement. Construit sur place à chaque envoi
  > par `bash tools/deploy.sh` depuis le PC ; `docker compose pull` ne suffit pas. Aucune donnée à
  > sauvegarder. Guide : `DEPLOIEMENT.md` dans le dossier du portfolio.
