# FlowSign - Traducteur Français ➔ LSF

Convertisseur intelligent de texte français vers la Langue des Signes Française, avec rendu 3D d'un avatar animé directement dans le navigateur.

Tu tapes une phrase, le moteur l'analyse, restructure les mots selon la syntaxe LSF (Temps + Sujet + Objet + Verbe) et l'avatar joue la séquence de signes en 3D. En temps réel, avec un effet karaoké pour suivre quel mot est en train d'être signé.

---

## Comment ça marche

Le projet tourne entièrement dans Docker. Trois conteneurs :

- **backend** — Flask + spaCy pour l'analyse linguistique, MongoDB pour stocker les signes disponibles
- **proxy** — nginx qui sert le frontend statique et redirige les appels `/api` vers Flask
- **mongodb** — la base qui contient les lemmes et les chemins vers les fichiers `.glb`

Au démarrage du backend, la BDD se synchronise automatiquement depuis le bucket OCI (Oracle Cloud) pour récupérer les animations disponibles.

---

## Stack technique

| Côté | Techno |
|------|--------|
| Frontend | HTML / CSS / JavaScript (Three.js pour la 3D) |
| Backend | Python, Flask, spaCy (`fr_core_news_sm`) |
| Base de données | MongoDB |
| Infra | Docker Compose, nginx, Oracle Cloud (bucket OCI) |

---

## Lancer le projet

**Prérequis** : avoir Docker et Docker Compose installés.

```bash
# Cloner le repo
git clone https://github.com/mehdiabdali/FlowSign.git
cd FlowSign/src

# Créer le fichier .env dans le dossier backend/
# (voir la section Variables d'environnement ci-dessous)

# Lancer tous les conteneurs
docker compose up --build
```

Le site est ensuite accessible sur `http://localhost` (branche `main`) ou sur `http://145.241.174.38/` (branche `reseaux`, déployé sur serveur).

---

## Variables d'environnement

À créer dans `src/backend/.env` :

```env
MONGO_URI=mongodb://mongodb:27017/flowsign
BUCKET_BASE_URL=https://objectstorage.eu-paris-1.oraclecloud.com/n/<namespace>/b/<bucket>/o/
FICHIER_JSON=/app/bdd_lsf.json
```

---

## Structure du projet

```
src/
├── backend/
│   ├── main.py           # API Flask, routes /api/traduire et /api/dictionnaire
│   ├── trad.py           # Moteur linguistique LSF (analyse spaCy + réordonnancement)
│   ├── CreationBDD.py    # Synchronisation depuis le bucket OCI
│   ├── populate_db.py    # Remplissage MongoDB depuis le JSON
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── main.js           # relie l'API, la 3D et le HTML
│   ├── scene.js          # Tout ce qui touche à Three.js et aux animations
│   ├── api.js            # Communication avec le backend Flask
│   ├── style.css
│   └── static/animations/  # Fichiers .glb (avatar + signes)
├── nginx/
│   └── nginx.conf
└── docker-compose.yml
```

---

## Ajouter des signes

Pour l'instant la base contient quelques mots de démo (BONJOUR, JE, MERCI, NON). Pour enrichir le vocabulaire :

1. Exporter l'animation du signe en `.glb`
2. Nommer le fichier avec le lemme en majuscules (ex: `MANGER.glb`)
3. Le déposer dans le bucket OCI dans `static/animations/`
4. Relancer le backend — la synchronisation se fait automatiquement au démarrage

---

## Auteur

Mehdi ABD ALI
Annabelle RIMBAUD
Gaspard CREMONINI
Paul-Malo POISSON
corantin berrux