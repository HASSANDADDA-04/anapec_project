import random

from app.ai.common import (
    INTERIM_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REPORTS_DIR,
    clean_text,
    domain_for,
    read_csv,
    write_csv,
    write_json,
)


def prepare() -> dict:
    report = {}
    occupations = {}
    seen_occupation = set()
    read_occupations = 0
    empty_occupations = 0
    outside_domain = 0
    for row in read_csv(RAW_DIR / "occupations_fr.csv"):
        read_occupations += 1
        uri = clean_text(row.get("conceptUri") or "", 400)
        label = clean_text(row.get("preferredLabel") or "", 300)
        isco = clean_text(row.get("iscoGroup") or "", 20)
        if not uri or len(label) < 2:
            empty_occupations += 1
            continue
        if uri in seen_occupation:
            continue
        seen_occupation.add(uri)
        domain = domain_for(isco)
        if not domain:
            outside_domain += 1
            continue
        description = clean_text(row.get("description") or "", 400)
        occupations[uri] = {
            "uri": uri,
            "label": label,
            "isco": isco,
            "domain": domain,
            "text": clean_text(f"{label}. {description}", 400),
        }

    skills = {}
    read_skills = 0
    empty_skills = 0
    for row in read_csv(RAW_DIR / "skills_fr.csv"):
        read_skills += 1
        uri = clean_text(row.get("conceptUri") or "", 400)
        label = clean_text(row.get("preferredLabel") or "", 300)
        if not uri or len(label) < 2:
            empty_skills += 1
            continue
        skills.setdefault(uri, label)

    relations = []
    seen_relation = set()
    read_relations = 0
    dropped_relations = 0
    for row in read_csv(RAW_DIR / "occupationSkillRelations_fr.csv"):
        read_relations += 1
        occupation_uri = clean_text(row.get("occupationUri") or "", 400)
        skill_uri = clean_text(row.get("skillUri") or "", 400)
        if occupation_uri not in occupations or skill_uri not in skills:
            dropped_relations += 1
            continue
        kind = clean_text(row.get("relationType") or "", 40).lower()
        kind = "essential" if "essential" in kind else "optional"
        key = (occupation_uri, skill_uri, kind)
        if key in seen_relation:
            dropped_relations += 1
            continue
        seen_relation.add(key)
        relations.append(
            {
                "occupation_uri": occupation_uri,
                "skill_uri": skill_uri,
                "relation": kind,
                "occupation_text": occupations[occupation_uri]["text"],
                "skill_label": skills[skill_uri],
                "domain": occupations[occupation_uri]["domain"],
            }
        )

    used_skills = {row["skill_uri"] for row in relations}
    skill_rows = [{"uri": uri, "label": label} for uri, label in sorted(skills.items()) if uri in used_skills]
    essential = [row for row in relations if row["relation"] == "essential"]
    by_occupation: dict[str, list[dict]] = {}
    for row in essential:
        by_occupation.setdefault(row["occupation_uri"], []).append(row)
    occupation_ids = list(by_occupation)
    random.Random(24).shuffle(occupation_ids)
    cut = int(len(occupation_ids) * 0.8)
    train_ids = set(occupation_ids[:cut])
    train_rows = [row for uri in train_ids for row in by_occupation[uri]]
    test_rows = [row for uri in occupation_ids[cut:] for row in by_occupation[uri]]

    fields = ["occupation_uri", "skill_uri", "relation", "occupation_text", "skill_label", "domain"]
    # 1. Sauvegarde des entités intermédiaires nettoyées (data/interim/)
    write_csv(INTERIM_DIR / "occupations.csv", list(occupations.values()), ["uri", "label", "isco", "domain", "text"])
    write_csv(INTERIM_DIR / "skills.csv", skill_rows, ["uri", "label"])
    write_csv(INTERIM_DIR / "relations.csv", relations, fields)

    # 2. Sauvegarde des jeux traités finaux (data/processed/)
    write_csv(PROCESSED_DIR / "occupations.csv", list(occupations.values()), ["uri", "label", "isco", "domain", "text"])
    write_csv(PROCESSED_DIR / "skills.csv", skill_rows, ["uri", "label"])
    write_csv(PROCESSED_DIR / "relations.csv", relations, fields)
    write_csv(PROCESSED_DIR / "train.csv", train_rows, fields)
    write_csv(PROCESSED_DIR / "test.csv", test_rows, fields)
    report = {
        "occupations_lues": read_occupations,
        "occupations_vides": empty_occupations,
        "occupations_hors_domaine": outside_domain,
        "occupations_gardees": len(occupations),
        "competences_lues": read_skills,
        "competences_vides": empty_skills,
        "competences_gardees": len(skill_rows),
        "liens_lus": read_relations,
        "liens_ecartes": dropped_relations,
        "liens_gardes": len(relations),
        "paires_entrainement": len(train_rows),
        "paires_test": len(test_rows),
        "metiers_entrainement": len(train_ids),
        "metiers_test": len(occupation_ids) - len(train_ids),
    }
    write_json(REPORTS_DIR / "clean_report.json", report)
    write_json(REPORTS_DIR / "metrics" / "clean_report.json", report)
    print(report)
    return report


if __name__ == "__main__":
    prepare()
