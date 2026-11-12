import random

import numpy as np

from app.ai.common import AI_DIR, read_csv, write_json
from app.services.matching import _encode


def _pairs(path):
    rows = list(read_csv(path))
    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(row["occupation_text"], []).append(row["skill_label"])
    return grouped


def _examples(grouped: dict[str, list[str]], skill_pool: list[str], seed: int):
    rng = random.Random(seed)
    positives = []
    negatives = []
    for text, labels in grouped.items():
        owned = set(labels)
        outsiders = [label for label in skill_pool if label not in owned] or skill_pool
        for label in labels:
            positives.append((text, label))
            negatives.append((text, rng.choice(outsiders)))
    return positives, negatives


def _best_threshold(positive_scores: np.ndarray, negative_scores: np.ndarray) -> tuple[float, dict]:
    best = None
    for step in range(20, 81):
        threshold = step / 100
        true_positive = int((positive_scores >= threshold).sum())
        true_negative = int((negative_scores < threshold).sum())
        false_positive = len(negative_scores) - true_negative
        false_negative = len(positive_scores) - true_positive
        total = len(positive_scores) + len(negative_scores)
        accuracy = (true_positive + true_negative) / total
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        current = {
            "seuil": threshold,
            "exactitude": round(accuracy, 4),
            "precision": round(precision, 4),
            "rappel": round(recall, 4),
            "f1": round(f1, 4),
        }
        if best is None or current["f1"] > best["f1"]:
            best = current
    return best["seuil"], best


def train() -> dict:
    grouped = _pairs(AI_DIR / "train.csv")
    skill_pool = sorted({label for labels in grouped.values() for label in labels})
    positives, negatives = _examples(grouped, skill_pool, seed=24)
    texts = sorted({text for pair in positives + negatives for text in pair})
    vectors = {text: vector for text, vector in zip(texts, _encode(texts))}
    positive_scores = np.array([float(vectors[left] @ vectors[right]) for left, right in positives])
    negative_scores = np.array([float(vectors[left] @ vectors[right]) for left, right in negatives])
    threshold, metrics = _best_threshold(positive_scores, negative_scores)
    ranking = float((positive_scores > negative_scores).mean())
    payload = {
        "seuil": threshold,
        "paires": len(positives),
        "classement": round(ranking, 4),
        "entrainement": metrics,
    }
    write_json(AI_DIR / "trained.json", payload)
    print(payload)
    return payload


if __name__ == "__main__":
    train()
