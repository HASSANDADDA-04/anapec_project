import pytest
from app.services.matching import fold, split_sentences
from app.ai.common import domain_for


def test_fold_accents():
    assert fold("Développeur Électronique") == "developpeur electronique"
    assert fold("Compétences Clés") == "competences cles"


def test_split_sentences():
    text = "Première phrase de présentation. Deuxième phrase avec des détails techniques • Troisième puce."
    parts = split_sentences(text)
    assert len(parts) >= 1
    assert any("Première" in p or "presentation" in fold(p) for p in parts)


def test_domain_for_isco():
    # ISCO 25xx -> Informatique
    assert domain_for("2512") == "Informatique"
    # ISCO 22xx -> Santé
    assert domain_for("2211") == "Santé"

