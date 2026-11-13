# 📖 Dictionnaire des Données — Projet ANAPEC

Ce document décrit l'ensemble des jeux de données, colonnes, types et significations selon la structure normalisée Cookiecutter Data Science.

---

## 1. Données Brutes (`data/raw/esco/`)

Classification européenne des aptitudes, compétences, certifications et professions (**ESCO v1.2.1** en français).

### `occupations_fr.csv` (Professions)
| Colonne | Type | Description |
| :--- | :--- | :--- |
| `conceptType` | `str` | Type d'entité ESCO (`Occupation`) |
| `conceptUri` | `str` | URI unique et immuable du métier dans l'ontologie ESCO |
| `iscoGroup` | `str` | Code de la classification internationale type des professions (CITP/ISCO-08) sur 1 à 4 chiffres |
| `preferredLabel` | `str` | Libellé normalisé officiel en français du métier |
| `altLabels` | `str` | Synonymes et appellations alternatives en français |
| `description` | `str` | Définition textuelle des responsabilités et missions du métier |

### `skills_fr.csv` (Compétences)
| Colonne | Type | Description |
| :--- | :--- | :--- |
| `conceptType` | `str` | Type d'entité ESCO (`Skill` / `Competence`) |
| `conceptUri` | `str` | URI unique de la compétence |
| `skillType` | `str` | Type (`skill/competence` ou `knowledge`) |
| `reuseLevel` | `str` | Niveau de transférabilité (`sector-specific`, `cross-sector`, `transversal`) |
| `preferredLabel` | `str` | Intitulé officiel de la compétence en français |
| `altLabels` | `str` | Formulations alternatives |
| `description` | `str` | Définition détaillée |

### `occupationSkillRelations_fr.csv` (Relations Métier-Compétence)
| Colonne | Type | Description |
| :--- | :--- | :--- |
| `occupationUri` | `str` | URI du métier lié |
| `skillUri` | `str` | URI de la compétence associée |
| `relationType` | `str` | Nature du lien : `essential` (essentielle) ou `optional` (optionnelle) |

---

## 2. Données Intermédiaires (`data/interim/`)

Tables obtenues après nettoyage, dédoublonnage et filtrage par les 12 domaines d'activité ANAPEC (`backend/app/ai/prepare.py`).

### `occupations.csv` (1 348 métiers filtrés)
- `uri` : Identifiant URI ESCO.
- `label` : Nom du métier.
- `isco` : Code ISCO.
- `domain` : Domaine ANAPEC attribué (ex : *Informatique*, *Santé*, *Commerce et vente*).
- `text` : Texte concaténé (`label. description`) utilisé pour le calcul vectoriel.

### `skills.csv` (9 893 compétences retenues)
- `uri` : Identifiant URI.
- `label` : Libellé de la compétence.

### `relations.csv` (55 872 relations validées)
- `occupation_uri`, `skill_uri`, `relation`, `occupation_text`, `skill_label`, `domain`.

---

## 3. Données Traitées (`data/processed/`)

Jeux d'apprentissage et de test finaux prêts pour les algorithmes ML.

### `train.csv` (Jeu d'entraînement — 23 239 paires)
- 80 % des métiers essentiels répartis de manière aléatoire reproductible (`seed=24`).
- Sert à l'optimisation du seuil de similarité cosinus via F1-Score.

### `test.csv` (Jeu de test — 6 062 paires)
- 20 % des métiers essentiels, complètement étanches du jeu d'entraînement.
- Utilisé par `evaluate.py` pour valider l'exactitude, la précision et le rappel sans surapprentissage.

---

## 4. Données Externes (`data/external/`)

- `data/external/hcp/activite-emploi-chomage-t3-2025.pdf` : Rapport officiel du Haut-Commissariat au Plan (HCP) du Maroc (indicateurs régionaux et sectoriels du chômage).
- `data/external/esco/occupations_multilingual.parquet` : Fichier Parquet multilingue complet pour d'éventuelles extensions de langues.

