.PHONY: help install data-prepare train evaluate esco-import docker-build docker-up docker-down test sonar-up sonar-scan sonar-down clean

help:
	@echo "=================================================================="
	@echo "                    PLATEFORME ANAPEC — MAKEFILE"
	@echo "=================================================================="
	@echo "Commandes disponibles :"
	@echo "  make install         Installe les dépendances backend et frontend"
	@echo "  make data-prepare    Nettoie et construit les jeux de données (raw -> processed)"
	@echo "  make train           Optimise le seuil de matching et génère models/matching/trained.json"
	@echo "  make evaluate        Évalue les performances sur le jeu de test (reports/metrics/)"
	@echo "  make esco-import     Importe la taxonomie ESCO dans PostgreSQL"
	@echo "  make test            Exécute les tests unitaires et génère reports/coverage.xml"
	@echo "  make docker-build    Construit les images Docker (backend, frontend)"
	@echo "  make docker-up       Démarre tous les conteneurs (db, backend, frontend)"
	@echo "  make docker-down     Arrête tous les conteneurs Docker"
	@echo "  make sonar-up        Démarre le serveur SonarQube (http://localhost:9001)"
	@echo "  make sonar-scan      Lance l'analyse de code SonarQube via conteneur CLI"
	@echo "  make sonar-down      Arrête le serveur SonarQube"
	@echo "  make clean           Supprime les fichiers temporaires et caches Python"
	@echo "=================================================================="

install:
	@echo "==> Installation des dépendances Backend..."
	pip install -r backend/requirements.txt
	@echo "==> Installation des dépendances Frontend..."
	cd frontend && npm install

data-prepare:
	@echo "==> Préparation des données (ESCO raw -> interim/processed)..."
	python -m backend.app.ai.prepare

train:
	@echo "==> Entraînement et optimisation du seuil de similarité..."
	python -m backend.app.ai.train

evaluate:
	@echo "==> Évaluation sur le jeu de test indépendant..."
	python -m backend.app.ai.evaluate

esco-import:
	@echo "==> Importation de la base ESCO dans PostgreSQL..."
	python -m backend.app.esco_import

test:
	@echo "==> Exécution des tests et calcul de la couverture..."
	pytest backend/tests --cov=backend/app --cov-report=xml:reports/coverage.xml --cov-report=term

docker-build:
	@echo "==> Construction des images Docker..."
	docker compose build

docker-up:
	@echo "==> Démarrage des services Docker..."
	docker compose up -d

docker-down:
	@echo "==> Arrêt des conteneurs..."
	docker compose down

sonar-up:
	@echo "==> Démarrage du serveur SonarQube sur http://localhost:9001..."
	docker compose --profile sonar up -d sonarqube

sonar-scan:
	@echo "==> Analyse statique et qualité du code via SonarScanner..."
	docker compose --profile sonar run --rm sonar-scanner

sonar-down:
	@echo "==> Arrêt du serveur SonarQube..."
	docker compose --profile sonar stop sonarqube sonar-scanner

clean:
	@echo "==> Nettoyage des caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
