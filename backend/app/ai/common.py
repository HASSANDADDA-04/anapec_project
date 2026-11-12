import csv
import json
import re
from pathlib import Path

from app.config import settings
from app.seed import DOMAINS

AI_DIR = Path(settings.esco_dir).resolve().parents[1] / "ai"
RAW_DIR = Path(settings.esco_dir)
MODELS_DIR = Path(settings.models_dir)
REPORTS_DIR = Path(settings.reports_dir)


def clean_text(value: str, limit: int = 500) -> str:
    text = (value or "").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def domain_for(isco: str) -> str:
    best_name = ""
    best_length = 0
    for name, _slug, prefixes in DOMAINS:
        for prefix in prefixes.split(","):
            if isco.startswith(prefix) and len(prefix) > best_length:
                best_name = name
                best_length = len(prefix)
    return best_name
