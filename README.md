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
├── Makefile                 # Automatisation standard des tâches (make help)
├── pyproject.toml           # Métadonnées du projet, dépendances & outillage
├── sonar-project.properties # Configuration de l'analyse SonarQube
├── docker-compose.yml       # Orchestration multi-conteneurs (Postgres, Backend, Frontend, SonarQube)
├── README.md                # Documentation principale du projet
│
├── data/                    # Découpage standard Cookiecutter Data Science
│   ├── raw/                 # Données originales et immuables
│   │   └── esco/            # Fichiers bruts ESCO v1.2.1 (occupations, skills, relations)
│   ├── interim/             # Données intermédiaires transformées & filtrées (12 domaines)
│   │   ├── occupations.csv  # 1 348 métiers retenus
│   │   ├── skills.csv       # 9 893 compétences associées
│   │   └── relations.csv    # 55 872 relations validées
│   ├── processed/           # Jeux de données finaux pour la modélisation
│   │   ├── train.csv        # 80 % des métiers pour l'entraînement (23 239 paires)
│   │   ├── test.csv         # 20 % des métiers pour l'évaluation (6 062 paires)
│   │   └── ...
│   └── external/            # Données externes complémentaires
│       ├── hcp/             # Rapport trimestriel du HCP Maroc
│       └── esco/            # Parquet multilingue & référentiels ISCO
│
├── models/                  # Structuration modulaire des modèles ML
│   ├── matching/            # Paramètres et seuils du moteur de matching
│   │   ├── trained.json     # Seuil optimal (0.26) et métriques F1
│   │   └── config.json      # Configuration de l'encodeur Sentence-Transformers
│   ├── checkpoints/         # Emplacement dédié aux points d'étape
│   └── embeddings/          # Cache vectoriel
│
├── reports/                 # Rapports et visualisations
│   ├── metrics/             # Rapports statistiques chiffrés
│   │   ├── clean_report.json# Rapport de filtrage et volumétrie
│   │   └── test_report.json # Performances du jeu de test (F1: 77.6 %)
│   └── figures/             # Graphiques et visualisations générées
│       ├── f1_vs_threshold.svg  # Courbe d'optimisation du seuil F1
│       ├── confusion_matrix.svg # Matrice de confusion détaillée
│       └── README.md
│
├── references/              # Dictionnaires et traçabilité des données
│   ├── SOURCES.txt          # Sources officielles et licences
│   ├── data_dictionary.md   # Dictionnaire complet des variables et colonnes
│   └── domains.md           # Les 12 domaines ANAPEC et correspondances ISCO-08
│
├── notebooks/               # Expérimentations & Exploration Jupyter
│   └── 01_data_exploration_and_matching.ipynb
│
├── backend/                 # API REST FastAPI & Moteur IA
│   ├── Dockerfile           # Conteneurisation Python 3.11 + Tesseract OCR
│   ├── requirements.txt     # Dépendances Python
│   ├── .env.example         # Configuration locale du backend
│   ├── tessdata/            # Fichiers de langues Tesseract (fra, eng)
│   ├── uploads/             # Stockage local des CVs déposés (ignoré par git)
│   ├── tests/               # Tests unitaires automatisés (pytest)
│   │   └── test_matching.py
│   └── app/
│       ├── main.py          # Point d'entrée FastAPI & initialisation
│       ├── config.py        # Configuration Pydantic Settings normalisée
│       ├── database.py      # Session et moteur SQLAlchemy
│       ├── models.py        # Modèles de données PostgreSQL
│       ├── security.py      # Authentification JWT & hachage des mots de passe
│       ├── seed.py          # Données de référence et comptes initiaux
│       ├── esco_import.py   # Script d'importation de la taxonomie ESCO
│       ├── ai/              # Pipeline Data Science & Entraînement
│       │   ├── common.py    # Chemins normalisés (raw, interim, processed, models)
│       │   ├── prepare.py   # Nettoyage et découpage train/test
│       │   ├── train.py     # Optimisation du seuil F1 de matching
│       │   └── evaluate.py  # Évaluation des métriques
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

## 🛡️ Qualité de Code & SonarQube

Le projet intègre **SonarQube** pour l'analyse statique du code, la détection des vulnérabilités de sécurité et la mesure de la couverture de tests.

### 1. Démarrer le serveur SonarQube
```bash
make sonar-up
# Ou via docker compose :
# docker compose --profile sonar up -d sonarqube
```
Le tableau de bord SonarQube est accessible sur [http://localhost:9001](http://localhost:9001) (identifiants par défaut : `admin` / `admin`).

### 2. Lancer l'analyse SonarScanner
```bash
# 1. Générer le rapport de couverture de tests :
make test

# 2. Exécuter l'analyse de code (FastAPI + React) :
make sonar-scan
```
La configuration d'analyse est gérée par le fichier [`sonar-project.properties`](file:///d:/EMSI%205IIR%20IA%20DATA/Deploiament%20%20app%20intelligente/Anapec_project/sonar-project.properties) qui cible le code métier (`backend/app`, `frontend/src`) et exclut automatiquement les dépendances et les datasets massifs.

### 3. Arrêter le serveur SonarQube
```bash
make sonar-down
```

---

## 🛠️ Technologies Utilisées

- **Frontend** : React 19, Vite 6, React Router 7, Vanilla CSS moderne.
- **Backend** : FastAPI, Uvicorn, SQLAlchemy 2, Pydantic v2 Settings.
- **Base de Données** : PostgreSQL 16.
- **OCR & Traitement Document** : Tesseract OCR, PyPDF, python-docx, Pillow.
- **NLP & Modèle IA** : HuggingFace `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`), NumPy.
- **Conteneurisation** : Docker, Docker Compose, Nginx Alpine.

