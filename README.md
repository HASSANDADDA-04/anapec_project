# 🇲🇦 Plateforme Intelligente ANAPEC

> **EMSI 5IIR — Déploiement d'une Application Intelligente**  
> Plateforme web d'aide au placement professionnel reliant candidats, entreprises et administrateurs avec analyse de CV, OCR et calcul de score de correspondance sémantique expliqué.

---

## 📌 Présentation du Projet

L'application **ANAPEC** permet d'automatiser et d'expliquer le matching entre profils de candidats et offres d'emploi :
1. **Extraction de CV multi-format** : Lecture directe de fichiers PDF et DOCX, avec fallback sur OCR (Tesseract) pour les scans ou documents complexes.
2. **Standardisation sémantique** : Alignement sur la taxonomie européenne **ESCO** (compétences, métiers et relations) dans 12 secteurs d'activité.
3. **Moteur d'IA explicable** : Calcul de similarité vectorielle par embeddings sémantiques (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) avec justification détaillée des compétences validées.
4. **Trois espaces dédiés** :
   - **Candidat** : Dépôt et correction du profil extrait, consultation des offres compatibles avec scores détaillés.
   - **Entreprise** : Publication d'offres et classement des candidatures reçues par pertinence.
   - **Administrateur** : Vue d'ensemble des utilisateurs, gestion des offres et statistiques globales.

---

## 🏗️ Architecture et Arborescence

Le projet adopte une structure hybride moderne combinant les standards **MLOps / Cookiecutter Data Science** et une architecture applicative **Fullstack** :

```text
Anapec_project/
├── .env.example             # Modèle des variables d'environnement
├── .gitignore               # Exclusions Git (venv, node_modules, cache, uploads)
├── docker-compose.yml       # Orchestration multi-conteneurs (Postgres, Backend, Frontend)
├── README.md                # Documentation principale du projet
│
├── backend/                 # API REST FastAPI & Moteur IA
│   ├── Dockerfile           # Conteneurisation Python 3.11 + Tesseract OCR
│   ├── requirements.txt     # Dépendances Python
│   ├── .env.example         # Configuration locale du backend
│   ├── tessdata/            # Fichiers de langues Tesseract (fra, eng)
│   ├── uploads/             # Stockage local des CVs déposés (ignoré par git)
│   └── app/
│       ├── main.py          # Point d'entrée FastAPI & initialisation
│       ├── config.py        # Configuration Pydantic Settings
│       ├── database.py      # Session et moteur SQLAlchemy
│       ├── models.py        # Modèles de données PostgreSQL
│       ├── security.py      # Authentification JWT & hachage des mots de passe
│       ├── seed.py          # Données de référence et comptes initiaux
│       ├── esco_import.py   # Script d'importation de la taxonomie ESCO
│       ├── ai/              # Pipeline Data Science & Entraînement
│       │   ├── common.py    # Utilitaires de données & chemins
│       │   ├── prepare.py   # Nettoyage et constitution du dataset
│       │   ├── train.py     # Optimisation du seuil de matching
│       │   └── evaluate.py  # Évaluation des métriques (Precision, Recall, F1)
│       ├── routers/         # Endpoints de l'API (Authentification, CV, Offres, Candidatures)
│       │   └── api.py
│       └── services/        # Logique métier
│           ├── extract.py   # Parsing PDF/DOCX et OCR Tesseract
│           └── matching.py  # Calcul sémantique & explications des scores
│
├── frontend/                # Application SPA React
│   ├── Dockerfile           # Build multi-stage (Node.js + Nginx)
│   ├── nginx.conf           # Configuration Nginx pour le routage SPA
│   ├── package.json         # Dépendances Node.js (React 19, Vite, React Router)
│   ├── vite.config.js       # Configuration du bundler Vite
│   └── src/
│       ├── main.jsx         # Point d'entrée React
│       ├── App.jsx          # Routes et vues (Candidat, Entreprise, Admin)
│       ├── api.js           # Client HTTP vers l'API Backend
│       └── styles.css       # Charte graphique & styles
│
├── data/                    # Jeux de données sources & préparés
│   ├── SOURCES.txt          # Traçabilité des sources officielles
│   ├── esco/                # Taxonomie ESCO (métiers, compétences, relations)
│   ├── ai/                  # Datasets préparés pour l'IA (train.csv, test.csv, relations.csv)
│   └── hcp/                 # Rapports statistiques du Haut-Commissariat au Plan
│
├── models/                  # Artefacts et métadonnées du modèle
│   └── trained.json         # Seuil optimal (0.26) et métriques d'apprentissage
│
├── reports/                 # Rapports d'évaluation et de nettoyage
│   ├── clean_report.json    # Rapport de filtrage et volumétrie des données
│   └── test_report.json     # Rapport de performance sur le jeu de test
│
└── docs/                    # Documentation académique
    ├── anapec demo.pdf      # Support de présentation du projet
    └── explication-projet.tex # Rapport détaillé en LaTeX
```

---

## 🚀 Démarrage Rapide

### Option A : Déploiement Complet avec Docker Compose (Recommandé)

Prérequis : [Docker Desktop](https://www.docker.com/) installé et lancé.

1. **Cloner le projet et copier l'environnement :**
   ```bash
   cp .env.example .env
   ```

2. **Lancer l'ensemble des services (Base de données + Backend + Frontend) :**
   ```bash
   docker compose up --build
   ```

3. **Accéder aux services :**
   - **Frontend (Interface Web)** : [http://localhost:5173](http://localhost:5173)
   - **Backend API & Swagger** : [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Base de données PostgreSQL** : `localhost:5433` (utilisateur : `anapec`, mdp : `anapec`)

---

### Option B : Lancement Manuel en Développement Local

#### 1. Démarrer la base PostgreSQL
```bash
docker compose up -d db
```

#### 2. Démarrer le Backend (FastAPI)
```bash
cd backend

# Créer et activer un environnement virtuel
python -m venv .venv
source .venv/bin/activate       # Sur Linux/macOS
.venv\Scripts\activate          # Sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base avec les données ESCO (optionnel si première exécution)
python -m app.esco_import

# Lancer le serveur de développement
uvicorn app.main:app --reload --port 8000
```

#### 3. Démarrer le Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
L'interface est accessible sur [http://localhost:5173](http://localhost:5173).

---

## 👥 Comptes de Démonstration (Pré-configurés)

La base de données est automatiquement initialisée au premier démarrage avec des comptes tests :

| Rôle | Email | Mot de passe | Description |
| :--- | :--- | :--- | :--- |
| **Administrateur** | `admin@anapec.test` | `Admin123` | Supervision globale, gestion des offres et comptes |
| **Entreprise** | `entreprise@anapec.test` | `Entreprise123` | Société Atlas — Création d'offres et évaluation des candidats |
| **Candidat** | `candidat1@anapec.test` | `Candidat123` | Profil candidat avec dépôt de CV |
| **Candidat** | `candidat2@anapec.test` | `Candidat123` | Deuxième profil candidat |

---

## 🧠 Pipeline Data Science & Entraînement

Pour recalculer les jeux de données et ré-optimiser les seuils :

```bash
cd backend

# 1. Nettoyage et construction des paires métier-compétences (génère data/ai/*.csv et reports/clean_report.json)
python -m app.ai.prepare

# 2. Recherche du meilleur seuil F1-score (génère models/trained.json)
python -m app.ai.train

# 3. Évaluation sur le jeu de test indépendant (génère reports/test_report.json)
python -m app.ai.evaluate
```

### Résultats obtenus :
- **Seuil de similarité optimal** : `0.26`
- **F1-Score** : `~78.8 %`
- **Précision** : `75.4 %`
- **Rappel** : `82.5 %`
- **Classement correct (ranking)** : `87.2 %`

---

## 🛠️ Technologies Utilisées

- **Frontend** : React 19, Vite 6, React Router 7, Vanilla CSS moderne.
- **Backend** : FastAPI, Uvicorn, SQLAlchemy 2, Pydantic v2 Settings.
- **Base de Données** : PostgreSQL 16.
- **OCR & Traitement Document** : Tesseract OCR, PyPDF, python-docx, Pillow.
- **NLP & Modèle IA** : HuggingFace `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`), NumPy.
- **Conteneurisation** : Docker, Docker Compose, Nginx Alpine.
