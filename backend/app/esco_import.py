import csv
from collections import defaultdict
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Domain, Occupation, OccupationSkill, Skill
from app.seed import seed_reference


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def _domain_for(isco: str, domains: list[Domain]) -> Domain | None:
    best = None
    best_length = 0
    for domain in domains:
        for prefix in domain.prefixes.split(","):
            if isco.startswith(prefix) and len(prefix) > best_length:
                best = domain
                best_length = len(prefix)
    return best


def import_esco(db: Session | None = None) -> dict:
    own_session = db is None
    db = db or SessionLocal()
    try:
        seed_reference(db)
        folder = Path(settings.esco_dir)
        if not (folder / "occupations_fr.csv").is_file():
            folder = Path(settings.raw_dir)
        domains = db.scalars(select(Domain)).all()
        occupations: dict[str, tuple[str, str, str, int]] = {}
        for row in _rows(folder / "occupations_fr.csv"):
            isco = (row.get("iscoGroup") or "").strip()
            domain = _domain_for(isco, domains)
            if domain is None:
                continue
            uri = row["conceptUri"].strip()
            occupations[uri] = (
                (row.get("preferredLabel") or "").replace("\n", " ").strip()[:300],
                isco,
                (row.get("description") or "").replace("\n", " ").strip()[:2000],
                domain.id,
            )

        needed_skills: set[str] = set()
        relations: list[tuple[str, str, str]] = []
        for row in _rows(folder / "occupationSkillRelations_fr.csv"):
            occupation_uri = (row.get("occupationUri") or "").strip()
            if occupation_uri not in occupations:
                continue
            skill_uri = (row.get("skillUri") or "").strip()
            if not skill_uri:
                continue
            needed_skills.add(skill_uri)
            relations.append((occupation_uri, skill_uri, (row.get("relationType") or "optional").strip()))

        skill_rows: dict[str, tuple[str, str]] = {}
        for row in _rows(folder / "skills_fr.csv"):
            uri = (row.get("conceptUri") or "").strip()
            if uri not in needed_skills:
                continue
            skill_rows[uri] = (
                (row.get("preferredLabel") or "").replace("\n", " ").strip()[:300],
                (row.get("skillType") or "")[:80],
            )

        db.execute(delete(OccupationSkill))
        db.execute(delete(Occupation))
        db.execute(delete(Skill))
        db.commit()
        print(f"occupations retenues: {len(occupations)}, competences: {len(skill_rows)}, liens: {len(relations)}", flush=True)

        skill_ids: dict[str, int] = {}
        pending: list[Skill] = []
        for uri, (label, skill_type) in skill_rows.items():
            pending.append(Skill(uri=uri, label=label or uri, skill_type=skill_type))
            if len(pending) >= 500:
                db.add_all(pending)
                db.flush()
                for skill in pending:
                    skill_ids[skill.uri] = skill.id
                pending = []
        if pending:
            db.add_all(pending)
            db.flush()
            for skill in pending:
                skill_ids[skill.uri] = skill.id

        occupation_ids: dict[str, int] = {}
        pending_occupations: list[Occupation] = []
        for uri, (label, isco, description, domain_id) in occupations.items():
            pending_occupations.append(
                Occupation(
                    uri=uri,
                    label=label or uri,
                    isco_group=isco,
                    description=description,
                    domain_id=domain_id,
                )
            )
            if len(pending_occupations) >= 500:
                db.add_all(pending_occupations)
                db.flush()
                for occupation in pending_occupations:
                    occupation_ids[occupation.uri] = occupation.id
                pending_occupations = []
        if pending_occupations:
            db.add_all(pending_occupations)
            db.flush()
            for occupation in pending_occupations:
                occupation_ids[occupation.uri] = occupation.id
        db.commit()

        seen = set()
        batch = []
        for occupation_uri, skill_uri, relation in relations:
            skill_id = skill_ids.get(skill_uri)
            occupation_id = occupation_ids.get(occupation_uri)
            if skill_id is None or occupation_id is None:
                continue
            key = (occupation_id, skill_id, relation)
            if key in seen:
                continue
            seen.add(key)
            batch.append(
                OccupationSkill(occupation_id=occupation_id, skill_id=skill_id, relation_type=relation[:20])
            )
            if len(batch) >= 2000:
                db.add_all(batch)
                db.commit()
                batch = []
        if batch:
            db.add_all(batch)
            db.commit()
        counts = {
            "occupations": len(occupation_ids),
            "skills": len(skill_ids),
            "relations": len(seen),
        }
        by_domain = defaultdict(int)
        for _, _, _, domain_id in occupations.values():
            by_domain[domain_id] += 1
        counts["domains_filled"] = len(by_domain)
        return counts
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    print(import_esco())
