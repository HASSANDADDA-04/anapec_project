<#
.SYNOPSIS
    Script d'automatisation PowerShell pour le projet ANAPEC (Équivalent de make pour Windows)
.EXAMPLE
    .\run.ps1 sonar-up
    .\run.ps1 sonar-scan
    .\run.ps1 docker-up
#>

param(
    [Parameter(Position=0)]
    [string]$Task = "help"
)

switch ($Task.ToLower()) {
    "help" {
        Write-Host "==================================================================" -ForegroundColor Cyan
        Write-Host "            PLATEFORME ANAPEC — COMMANDES POWERSHELL" -ForegroundColor Cyan
        Write-Host "==================================================================" -ForegroundColor Cyan
        Write-Host "Commandes disponibles :"
        Write-Host "  .\run.ps1 sonar-up        Démarre le serveur SonarQube sur http://localhost:9001" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 sonar-scan      Lance l'analyse de code SonarQube via Docker" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 sonar-down      Arrête le serveur SonarQube" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 docker-up       Démarre tous les services (db, backend, frontend)" -ForegroundColor Green
        Write-Host "  .\run.ps1 docker-down     Arrête tous les conteneurs Docker" -ForegroundColor Green
        Write-Host "  .\run.ps1 docker-build    Construit les images Docker" -ForegroundColor Green
        Write-Host "  .\run.ps1 test            Exécute les tests unitaires et génère reports/coverage.xml" -ForegroundColor Magenta
        Write-Host "  .\run.ps1 data-prepare    Nettoie et construit les jeux de données (raw -> processed)"
        Write-Host "  .\run.ps1 train           Optimise le seuil de similarité"
        Write-Host "  .\run.ps1 evaluate        Évalue sur le jeu de test indépendant"
        Write-Host "==================================================================" -ForegroundColor Cyan
    }
    "sonar-up" {
        Write-Host "==> Démarrage du serveur SonarQube sur http://localhost:9001..." -ForegroundColor Cyan
        docker compose --profile sonar up -d sonarqube
    }
    "sonar-scan" {
        Write-Host "==> Lancement de l'analyse SonarScanner..." -ForegroundColor Cyan
        docker compose --profile sonar run --rm sonar-scanner
    }
    "sonar-down" {
        Write-Host "==> Arrêt du serveur SonarQube..." -ForegroundColor Cyan
        docker compose --profile sonar stop sonarqube sonar-scanner
    }
    "docker-up" {
        Write-Host "==> Démarrage des conteneurs applicatifs..." -ForegroundColor Green
        docker compose up -d
    }
    "docker-down" {
        Write-Host "==> Arrêt des conteneurs applicatifs..." -ForegroundColor Green
        docker compose down
    }
    "docker-build" {
        Write-Host "==> Construction des images Docker..." -ForegroundColor Green
        docker compose build
    }
    "test" {
        Write-Host "==> Exécution des tests pytest..." -ForegroundColor Magenta
        pytest backend/tests --cov=backend/app --cov-report=xml:reports/coverage.xml --cov-report=term
    }
    "data-prepare" {
        python -m backend.app.ai.prepare
    }
    "train" {
        python -m backend.app.ai.train
    }
    "evaluate" {
        python -m backend.app.ai.evaluate
    }
    default {
        Write-Host "Commande inconnue : '$Task'. Tapez '.\run.ps1 help' pour la liste des commandes." -ForegroundColor Red
    }
}

