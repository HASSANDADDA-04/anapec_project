import json

import numpy as np

from app.ai.common import AI_DIR, MODELS_DIR, REPORTS_DIR, write_json
from app.ai.train import _examples, _pairs
from app.services.matching import _encode


def evaluate() -> dict:
    trained_path = MODELS_DIR / "trained.json"
    if not trained_path.is_file():
        trained_path = AI_DIR / "trained.json"
    trained = json.loads(trained_path.read_text(encoding="utf-8"))
    threshold = float(trained["seuil"])
    grouped = _pairs(AI_DIR / "test.csv")
    skill_pool = sorted({label for labels in grouped.values() for label in labels})
    positives, negatives = _examples(grouped, skill_pool, seed=91)
    texts = sorted({text for pair in positives + negatives for text in pair})
    vectors = {text: vector for text, vector in zip(texts, _encode(texts))}
    positive_scores = np.array([float(vectors[left] @ vectors[right]) for left, right in positives])
    negative_scores = np.array([float(vectors[left] @ vectors[right]) for left, right in negatives])
    true_positive = int((positive_scores >= threshold).sum())
    true_negative = int((negative_scores < threshold).sum())
    false_positive = len(negative_scores) - true_negative
    false_negative = len(positive_scores) - true_positive
    total = len(positive_scores) + len(negative_scores)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
    payload = {
        "seuil": threshold,
        "paires_test": len(positive_scores),
        "exactitude": round((true_positive + true_negative) / total, 4),
        "precision": round(precision, 4),
        "rappel": round(recall, 4),
        "classement": round(float((positive_scores > negative_scores).mean()), 4),
    }
    write_json(REPORTS_DIR / "test_report.json", payload)
    print(payload)
    return payload


if __name__ == "__main__":
    evaluate()
