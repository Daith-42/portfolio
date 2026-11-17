"""Génère la version anglaise du site (en/index.html) à partir de la page française.

Usage : py tools/build-en.py           écrit en/index.html
        py tools/build-en.py --check   vérifie seulement qu'elle est à jour (utilisé par check-site.py)

Principe : la page anglaise n'est jamais modifiée à la main. Chaque texte français doit avoir sa
traduction dans les tables ci-dessous. S'il en manque une (texte ajouté ou modifié côté français),
le script s'arrête et affiche les phrases à traduire : les deux langues ne peuvent pas diverger.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT = ROOT / "en" / "index.html"
SITE = "https://david-ameline.daith42.fr"

# ---------------------------------------------------------------------------
# 1. Blocs avec balises internes (traduits d'un seul tenant pour garder un ordre naturel)
# ---------------------------------------------------------------------------
BLOCKS = [
    ("""            Étudiant en informatique à SUPINFO, je cherche un <strong>stage</strong> pour l'été 2027,
            puis une <strong>alternance</strong> à partir de septembre 2027, pour gagner en expérience sur des projets concrets.""",
     """            IT student at SUPINFO, I'm looking for an <strong>internship</strong> for summer 2027,
            then a <strong>work-study placement</strong> from September 2027, to gain experience on real projects."""),
    ("""Il faut <del>corigé</del> <ins>corriger</ins> les <del>fote</del> <ins>fautes</ins> sans quitter sa fenêtre""",
     """It <del>fixs</del> <ins>fixes</ins> your <del>speling</del> <ins>spelling</ins> without leaving the window"""),
    ("""<li><strong>Import du relevé bancaire</strong> au format CSV, avec un aperçu à valider avant l'enregistrement</li>""",
     """<li><strong>Bank statement import</strong> in CSV format, with a preview to approve before saving</li>"""),
    ("""<li><strong>Moteur de règles</strong> : un mot-clé dans le libellé donne une catégorie, appliquée automatiquement à chaque import</li>""",
     """<li><strong>Rules engine</strong>: a keyword in the label sets a category, applied automatically on every import</li>"""),
    ("""<li><strong>Tableau de bord</strong> et totaux par catégorie et par mois</li>""",
     """<li><strong>Dashboard</strong> and totals by category and by month</li>"""),
    ("""<li><strong>Grand livre</strong> de toutes les opérations, modifiables à la main</li>""",
     """<li><strong>Ledger</strong> of every transaction, editable by hand</li>"""),
    ("""<li><strong>Historique des imports</strong>, avec la possibilité d'annuler un import complet</li>""",
     """<li><strong>Import history</strong>, with the option to undo a whole import</li>"""),
    ("""<li><strong>Export Excel</strong> des opérations</li>""",
     """<li><strong>Excel export</strong> of transactions</li>"""),
    ("""<li><strong>De 2 à 4 joueurs</strong>, sur le même ordinateur ou en <strong>réseau local</strong>, ou seul face à une <strong>IA</strong> à deux niveaux</li>""",
     """<li><strong>2 to 4 players</strong>, on the same computer or over a <strong>local network</strong>, or solo against an <strong>AI</strong> with two levels</li>"""),
    ("""<li><strong>Deux modes</strong> : classique (4 plateaux) et personnalisé (3 à 6 plateaux, cases placées au hasard)</li>""",
     """<li><strong>Two modes</strong>: classic (4 boards) and custom (3 to 6 boards, randomly placed squares)</li>"""),
    ("""<li><strong>4 thèmes graphiques</strong>, chacun avec ses musiques et ses effets sonores</li>""",
     """<li><strong>4 visual themes</strong>, each with its own music and sound effects</li>"""),
    ("""<li><strong>5 langues</strong> : français, anglais, espagnol, italien et allemand</li>""",
     """<li><strong>5 languages</strong>: French, English, Spanish, Italian and German</li>"""),
    ("""<li><strong>L'interface graphique</strong> : lanceur, pages de profil et d'options, affichage des plateaux, préparation de la partie et boucle de jeu à l'écran</li>""",
     """<li><strong>The graphical interface</strong>: launcher, profile and settings pages, board display, game setup and the on-screen game loop</li>"""),
    ("""<li><strong>L'intégration dans l'interface</strong> de l'IA, du passage de tour, du lancement rapide et du mode triche</li>""",
     """<li><strong>Wiring into the interface</strong> the AI, turn skipping, quick start and cheat mode</li>"""),
    ("""<li><strong>Les visuels par thème</strong> (pions, cases bonus, trous, barrières) et l'écran de fin de partie</li>""",
     """<li><strong>Per-theme visuals</strong> (pawns, bonus squares, holes, barriers) and the end-of-game screen</li>"""),
    ("""<li><strong>La correction de bugs</strong>, notamment en partie en réseau</li>""",
     """<li><strong>Bug fixing</strong>, especially in network games</li>"""),
]

# ---------------------------------------------------------------------------
# 2. Textes simples (contenu des balises), français → anglais
# ---------------------------------------------------------------------------
TEXT = {
    "David Ameline · Stage et alternance en informatique 2027": "David Ameline · IT internship & work-study 2027",
    "Aller au contenu": "Skip to content",
    "Projets": "Projects",
    "Parcours": "Experience",
    "Compétences": "Skills",
    "Au-delà du code": "Beyond code",
    "Me contacter": "Contact me",
    "Étudiant · SUPINFO · 2e année": "Student · SUPINFO · 2nd year",
    "Trois stages en informatique, dont un au Ministère des Armées, et un serveur Linux que j'administre et sécurise moi-même. Je m'intéresse autant au développement qu'aux systèmes et à la cybersécurité.":
        "Three IT internships, including one at the French Ministry of the Armed Forces, and a Linux server I run and secure myself. I'm as interested in development as in systems and cybersecurity.",
    "M'écrire un mail": "Email me",
    "Voir mes projets": "See my projects",
    "Fiche candidat": "Candidate profile",
    "Disponible": "Available",
    "Ouvert à": "Open to",
    "Développement · Systèmes · Cybersécurité": "Development · Systems · Cybersecurity",
    "Stage": "Internship",
    "Juin → sept. 2027": "June → Sept. 2027",
    "2 mois minimum": "2 months minimum",
    "Alternance": "Work-study",
    "Dès sept. 2027": "From Sept. 2027",
    "1 semaine / 1 semaine": "1 week school / 1 week work",
    "Lieu": "Location",
    "Tours · Région parisienne": "Tours · Paris region",
    "Langues": "Languages",
    "Français · Anglais B1": "French · English B1",
    "Une sélection. Le reste est sur mon GitHub, avec bien d'autres.": "A selection. There is more on my GitHub.",
    "posture de sécurité": "security posture",
    "Ports ouverts sur Internet": "Ports open to the Internet",
    "VPN uniquement": "VPN only",
    "clé uniquement": "key only",
    "Publication": "Publishing",
    "tunnel sortant": "outbound tunnel",
    "Réseau public Docker": "Public Docker network",
    "isolé": "isolated",
    "Conteneurs": "Containers",
    "non-root, lecture seule": "non-root, read-only",
    "Mises à jour de sécurité": "Security updates",
    "automatiques": "automatic",
    "Réseau · Sécurité": "Network · Security",
    "Déploiement continu": "Continuous deployment",
    "Mon serveur auto-hébergé : un ancien portable reconverti sous Ubuntu Server, qui fait tourner tous mes projets, dont ce portfolio.":
        "My self-hosted server: an old laptop turned into an Ubuntu Server machine that runs all my projects, including this portfolio.",
    "Aucun port ouvert sur Internet : administration par VPN, publication par tunnel Cloudflare, réseau Docker public isolé, conteneurs durcis, supervision avec alertes.":
        "No port open to the Internet: admin over VPN, publishing through a Cloudflare tunnel, an isolated public Docker network, hardened containers, monitoring with alerts.",
    "Héberge mes projets": "Hosts my projects",
    "Jeu · Édition collector": "Game · Collector's edition",
    "Coffret édition limitée": "Limited edition box set",
    "Scellé": "Sealed",
    "Complet": "Complete",
    "Ma collection": "My collection",
    "128 objets": "128 items",
    "En développement": "In development",
    "Catalogue des objets Zelda et gestionnaire de collection, en français et en anglais, avec recherche, comptes membres et back-office.":
        "A catalogue of Zelda collectibles and a collection manager, in French and English, with search, member accounts and an admin back office.",
    "Développé avec un assistant de code IA : je définis le besoin, je fais les choix d'architecture, puis je relis et teste chaque évolution.":
        "Built with an AI coding assistant: I define the needs and make the architecture choices, then review and test every change.",
    "Projet perso · 2026": "Personal project · 2026",
    "Mise en ligne prévue": "Launch planned",
    "Dépenses · oct.": "Spending · Oct.",
    "842,60 €": "€842.60",
    "Application de suivi de mes dépenses mensuelles : import des relevés bancaires, classement automatique par règles, tableau de bord par catégorie et export.":
        "An app to track my monthly spending: bank statement import, rule-based categorisation, a dashboard by category and export.",
    "Projet perso": "Personal project",
    "Détails": "Details",
    "Outil Windows": "Windows tool",
    "Programme de correction automatique de l'orthographe sous Windows : le texte se corrige directement dans l'application où l'on tape.":
        "Automatic spelling correction for Windows: text gets fixed right inside the app you are typing in.",
    "Voir le projet": "View project",
    "Site portfolio réalisé en binôme avec une designer UI/UX : elle a conçu les maquettes, j'ai développé le rendu en Astro.":
        "Portfolio website built with a UI/UX designer: she designed the mockups, I built the site in Astro.",
    "Voir le site": "Visit site",
    "Autres projets": "Other projects",
    "Jeu de plateau en Python, réalisé à quatre pour le projet de fin de 1re année à SUPINFO.":
        "Board game in Python, built by a team of four for the end-of-first-year project at SUPINFO.",
    "Expériences en informatique": "IT experience",
    "Juin → août 2026": "June → Aug. 2026",
    "Développeur web Vue3": "Vue3 web developer",
    "Ministère des Armées · stage de fin de 1re année": "French Ministry of the Armed Forces · end-of-first-year internship",
    "Développement d'un démonstrateur d'API en Vue3.": "Built an API demonstrator in Vue3.",
    "Avril → juin 2026": "Apr. → June 2026",
    "Intégrateur Web Analytics": "Web analytics integrator",
    "Aptimiz · stage à temps partiel": "Aptimiz · part-time internship",
    "Installation de Google Analytics et mise en place d'un tracking complet du site.": "Set up Google Analytics and full website tracking.",
    "Août 2024": "Aug. 2024",
    "Développeur web junior": "Junior web developer",
    "Développement de fonctionnalités web en HTML, CSS et JavaScript.": "Built web features in HTML, CSS and JavaScript.",
    "Formation": "Education",
    "En cours": "In progress",
    "Baccalauréat général": "French Baccalaureate (general)",
    "Obtenu": "Completed",
    "Mention assez bien": "With honours (“assez bien”)",
    "Prévention et secours civiques, niveau 1": "French first-aid certificate, level 1",
    "En parallèle : travaux agricoles chaque été": "Alongside: farm work every summer",
    "Étés 2025 et 2026": "Summers 2025 and 2026",
    "Ouvrier agricole": "Farm worker",
    "Tri visuel et gestion de semences · Agri-Obtention": "Visual sorting and seed handling · Agri-Obtention",
    "Juillets 2024 et 2025": "July 2024 and 2025",
    "Travaux agricoles": "Farm work",
    "Moisson, ferme familiale à Prunay-en-Yvelines · Earl Gohervilla": "Harvest on a family farm in Prunay-en-Yvelines · Earl Gohervilla",
    "Juillet 2023": "July 2023",
    "Castrage de maïs dans le Lot · Scea Brugidou": "Maize detasseling in the Lot · Scea Brugidou",
    "Développement web": "Web development",
    "Programmation": "Programming",
    "Systèmes, réseau et sécurité": "Systems, network and security",
    "Durcissement SSH": "SSH hardening",
    "Pare-feu UFW / iptables": "UFW / iptables firewall",
    "Segmentation réseau": "Network segmentation",
    "Supervision et alertes": "Monitoring and alerting",
    "En-têtes de sécurité (CSP)": "Security headers (CSP)",
    "Transverses, qualités et langues": "Soft skills and languages",
    "Gestion de projet": "Project management",
    "Méthodes agiles": "Agile methods",
    "Droit, propriété intellectuelle": "Law, intellectual property",
    "Déterminé": "Determined",
    "Organisé": "Organised",
    "Curieux": "Curious",
    "Français": "French",
    "Anglais B1": "English B1",
    "Engagements": "Involvement",
    "Ambassadeur SUPINFO": "SUPINFO ambassador",
    "Portes ouvertes, salons, parrain lors des journées d'immersion.": "Open days, education fairs, mentor during immersion days.",
    "Association du lycée qui parle de consentement et accompagne les plus jeunes sur les questions de sexualité.":
        "High school association that talks about consent and supports younger students on questions of sexuality.",
    "Centres d'intérêt": "Interests",
    "Randonnée": "Hiking",
    "· Bivouac en haute montagne": "· High-mountain bivouacs",
    "Vélo": "Cycling",
    "· Rénovation, bikepacking": "· Restoring bikes, bikepacking",
    "Course": "Running",
    "· Les 20 km de Tours en préparation": "· Training for the Tours 20 km",
    "Guitare": "Guitar",
    "· Depuis plusieurs années": "· For several years",
    "Apnée": "Freediving",
    "· En piscine et en mer": "· In the pool and at sea",
    "Escalade": "Climbing",
    "· En salle": "· Indoor",
    "Culture japonaise": "Japanese culture",
    "Agrandir": "Enlarge",
    "Mon parcours sur une page": "My background on one page",
    "Formation, expériences, compétences, projets et centres d'intérêt, au format PDF.": "Education, experience, skills, projects and interests, as a PDF. The CV is in French.",
    "Télécharger le CV": "Download my CV",
    "Aperçu": "Preview",
    "PDF · 1 page": "PDF · 1 page · in French",
    "Un stage ou une alternance à proposer ?": "An internship or work-study placement to offer?",
    "Je réponds vite par mail ou par téléphone. Mes projets sont sur GitHub, mon parcours sur LinkedIn.":
        "I reply quickly by email or phone. My projects are on GitHub, my background on LinkedIn.",
    "Mail": "Email",
    "Téléphone": "Phone",
    "Afficher le numéro": "Show number",
    "Une application personnelle de suivi des dépenses. J'importe le relevé de mon compte, les opérations se classent toutes seules par catégorie, et je suis mes dépenses mois par mois dans un tableau de bord.":
        "A personal spending tracker. I import my bank statement, transactions sort themselves into categories, and I follow my spending month by month on a dashboard.",
    "Ce qu'elle fait": "What it does",
    "Comment c'est construit": "How it's built",
    "API Python avec Flask, base SQLite, pandas pour lire les relevés et produire l'export Excel": "Python API with Flask, SQLite database, pandas to read statements and produce the Excel export",
    "Vue 3 avec Vue Router, Vite et Tailwind CSS 4": "Vue 3 with Vue Router, Vite and Tailwind CSS 4",
    "Lancement": "Startup",
    "Un script démarre l'API et l'interface puis ouvre le navigateur ; l'interface relaie ses appels vers l'API": "A script starts the API and the interface, then opens the browser; the interface proxies its calls to the API",
    "Code source privé": "Private source code",
    "Fermer": "Close",
    "Projet de 1re année SUPINFO · 2026": "SUPINFO first-year project · 2026",
    "Jeu de plateau en Python, réalisé à quatre pour le projet de fin de première année (1PROJ). Chaque joueur place ses taupes dans les trous de plusieurs plateaux successifs ; celui qui occupe le dernier trou gagne la partie.":
        "A board game in Python, built by a team of four for the end-of-first-year project (1PROJ). Players move their moles into the holes of several boards in a row; whoever takes the very last hole wins.",
    "Le jeu": "The game",
    "Ma part": "My part",
    "Langage": "Language",
    "Python, avec une séparation entre la logique du jeu, l'interface, le son et le réseau": "Python, with game logic, interface, sound and networking kept separate",
    "Tkinter, et Pillow pour les images": "Tkinter, with Pillow for images",
    "Son": "Sound",
    "miniaudio pour les musiques et les effets": "miniaudio for music and sound effects",
    "Équipe": "Team",
    "4 étudiants, travail en branches et pull requests sur GitHub": "4 students, working with branches and pull requests on GitHub",
    "Voir le code": "View code",
    "CV de David Ameline": "David Ameline's CV",
    "Télécharger le PDF": "Download the PDF",
    "© 2026 · Étudiant en informatique à SUPINFO, en recherche d'un stage et d'une alternance":
        "© 2026 · IT student at SUPINFO, looking for an internship and a work-study placement",
}

# Attributs traduisibles (alt, aria-label, title, content des métadonnées, libellés du menu)
ATTR = {
    "Portfolio de David Ameline, étudiant en informatique à SUPINFO : développement, systèmes et sécurité. Cherche un stage (juin à sept. 2027) puis une alternance.":
        "Portfolio of David Ameline, IT student at SUPINFO: development, systems and security. Looking for an internship (June–Sept. 2027), then a work-study placement.",
    "David Ameline · Stage et alternance en informatique 2027": "David Ameline · IT internship & work-study 2027",
    "Étudiant en informatique à SUPINFO, en recherche d'un stage (juin à septembre 2027) puis d'une alternance (1 semaine / 1 semaine). Développement, systèmes, cybersécurité.":
        "IT student at SUPINFO, looking for an internship (June to September 2027), then a work-study placement (1 week school / 1 week work). Development, systems, cybersecurity.",
    "Étudiant en informatique à SUPINFO, en recherche d'un stage puis d'une alternance dès 2027. Développement, systèmes, cybersécurité.":
        "IT student at SUPINFO, looking for an internship then a work-study placement from 2027. Development, systems, cybersecurity.",
    "David Ameline, étudiant en informatique en recherche d'un stage et d'une alternance dès 2027":
        "David Ameline, IT student looking for an internship and a work-study placement from 2027",
    "English version": "Version française",
    "Ouvrir le menu": "Open menu",
    "Fermer le menu": "Close menu",
    "Afficher le projet": "Show project",
    "Masquer": "Hide",
    "Fiche de disponibilité": "Availability",
    "Logo Corafolio": "Corafolio logo",
    "Agrandir l'aperçu du CV": "Enlarge the CV preview",
    "Fermer": "Close",
    "CV de David Ameline : formation, expériences, compétences, projets et centres d'intérêt":
        "David Ameline's CV (in French): education, experience, skills, projects and interests",
}

# Identiques dans les deux langues (noms propres, technos, chiffres)
KEEP = {
    "David Ameline", "Sections", "CV", "Contact", "asushome1", "Administration", "SSH", "0", "Linux · Docker",
    "Homelab · 2026", "Zelda Collection", "FR · EN", "PAL-FR · 2011", "Next.js · TypeScript", "PostgreSQL · Docker",
    "D-Wallet", "Vue3 · Vite", "Python · Flask", "AutoHotkey", "OrthoAutoAI", "Astro", "UI/UX", "Corafolio",
    "coralinechapeau.gitlab.io", "Collaboration", "1PROJ", "Python", "Quatrian Inc. · Canada", "Master of Engineering",
    "SUPINFO", "· 2025–2030", "PSC1", "HTML / CSS", "JavaScript", "TypeScript", "PHP", "Vue3", "React", "Laravel",
    "Symfony", "C", "C++", "Java", "SQL", "Linux (Ubuntu Server)", "Windows Server", "Docker", "VPN Tailscale",
    "Cloudflare Tunnel · Zero Trust", "DNS · DNSSEC · DMARC", "Team Intime", "GitHub", "LinkedIn",
    "github.com/Daith-42", "linkedin.com/in/david-ameline", "david.ameline42", "@gmail.com", "Backend", "Frontend",
    "Interface", "A Mole in the Hole", "✓", "FR",
}
KEEP_ATTR = {"Sections", "David Ameline", "width=device-width, initial-scale=1", "index, follow, max-image-preview:large"}


def translate(fr: str) -> str:
    s = fr
    problems = []

    # --- structure de la page ---
    def must(old, new, count=1):
        nonlocal s
        n = s.count(old)
        if n != count:
            problems.append(f"structure introuvable ({n}×) : {old[:70]}")
        s = s.replace(old, new)

    must('<html lang="fr">', '<html lang="en">')
    must(f'<link rel="canonical" href="{SITE}/">', f'<link rel="canonical" href="{SITE}/en/">')
    must(f'<meta property="og:url" content="{SITE}/">', f'<meta property="og:url" content="{SITE}/en/">')
    must('<meta property="og:locale" content="fr_FR">\n  <meta property="og:locale:alternate" content="en_GB">',
         '<meta property="og:locale" content="en_GB">\n  <meta property="og:locale:alternate" content="fr_FR">')
    must(f'{SITE}/og-image.png', f'{SITE}/og-image-en.png', 3)
    en_img = ROOT / "og-image-en.png"
    if en_img.exists():  # l'empreinte copiée depuis la page française est celle de l'image française
        import hashlib
        fp = hashlib.sha256(en_img.read_bytes()).hexdigest()[:8]
        s = re.sub(r'og-image-en[.]png[?]v=[0-9a-f]+', 'og-image-en.png?v=' + fp, s)
    must('<a class="lang-switch" href="/en/" hreflang="en" lang="en" aria-label="English version">EN</a>',
         '<a class="lang-switch" href="/" hreflang="fr" lang="fr" aria-label="English version">FR</a>')
    # fichiers locaux en chemins absolus (la page est servie depuis /en/)
    s = re.sub(r'(href|src)="(?!/|https?:|mailto:|#|data:)', r'\1="/', s)

    # données structurées
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', s, re.S)
    data = json.loads(m.group(2))
    data["@id"] = f"{SITE}/en/#page"
    data["url"] = f"{SITE}/en/"
    data["name"] = TEXT["David Ameline · Stage et alternance en informatique 2027"]
    data["inLanguage"] = "en-GB"
    person = data["mainEntity"]
    person["jobTitle"] = "IT student"
    person["description"] = ("Second-year IT student at SUPINFO, looking for an internship from June to September 2027, "
                             "then a work-study placement (1 week school / 1 week work) from September 2027. "
                             "Interested in development, system administration and cybersecurity.")
    person["knowsAbout"] = ["Web development", "Vue.js", "React", "Laravel", "PHP", "TypeScript", "Python", "C", "Java",
                            "SQL", "Linux", "System administration", "Docker", "Networking", "Systems security"]
    block = json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    s = s[:m.start(2)] + "\n  " + block + "\n  " + s[m.end(2):]

    # --- blocs avec balises internes ---
    for fr_block, en_block in BLOCKS:
        if fr_block not in s:
            problems.append(f"bloc français introuvable : {fr_block.strip()[:70]}")
        s = s.replace(fr_block, en_block)
    en_segments = {t.strip() for _, en in BLOCKS for t in re.findall(r">?([^<>]+)<?", en) if t.strip()}

    # --- attributs ---
    def attr_sub(m):
        name, val = m.group(1), m.group(2)
        if not re.search(r"[A-Za-zÀ-ÿ]{2}", val) or val.startswith(("http", "/", "#", "mailto:", "tel:")):
            return m.group(0)
        if name == "content" and not re.search(r"\s", val):  # noms, couleurs, locales…
            return m.group(0)
        if val in ATTR:
            return f'{name}="{ATTR[val]}"'
        if val in KEEP_ATTR or val in ATTR.values():
            return m.group(0)
        problems.append(f'attribut {name} sans traduction : "{val}"')
        return m.group(0)
    s = re.sub(r'\b(alt|aria-label|title|content|data-label-open|data-label-close|data-label-more|data-label-less)="([^"]*)"', attr_sub, s)

    # --- textes entre balises (hors scripts) ---
    parts = re.split(r"(<script.*?</script>|<style.*?</style>)", s, flags=re.S)
    for i in range(0, len(parts), 2):
        def text_sub(m):
            raw = m.group(1)
            txt = raw.strip()
            if not txt or not re.search(r"[A-Za-zÀ-ÿ0-9✓€]", txt):
                return m.group(0)
            if txt in TEXT:
                return ">" + raw.replace(txt, TEXT[txt]) + "<"
            if txt in KEEP or txt in TEXT.values() or txt in en_segments:
                return m.group(0)
            problems.append(f'texte sans traduction : "{txt}"')
            return m.group(0)
        parts[i] = re.sub(r">([^<]+)<", text_sub, parts[i])
    s = "".join(parts)

    s = s.replace("<!-- ", "<!-- [EN généré par tools/build-en.py, ne pas modifier à la main] ", 1)
    return s, problems


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    en, problems = translate(SRC.read_text(encoding="utf-8"))
    if problems:
        print("Traductions manquantes ou structure modifiée :")
        for p in problems:
            print("  -", p)
        print("Complète les tables de tools/build-en.py.")
        sys.exit(1)
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != en:
            print("en/index.html n'est pas à jour : lance py tools/build-en.py")
            sys.exit(1)
        print("en/index.html à jour")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(en, encoding="utf-8", newline="\n")
    print(f"écrit : {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
