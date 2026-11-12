import re
import unicodedata

import numpy as np

THRESHOLD = 0.62
DIPLOMA_RANK = {
    "": 0,
    "aucun": 0,
    "bac": 1,
    "bac+2": 2,
    "bac+3": 3,
    "bac+5": 4,
    "doctorat": 5,
}

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"[\n\.;•]+", text)
    sentences = [chunk.strip() for chunk in chunks if len(chunk.strip()) > 12]
    return sentences[:40] or [text[:500]]


def _encode(texts: list[str]) -> np.ndarray:
    vectors = get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors)


def fold(text: str) -> str:
    value = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(char for char in value if unicodedata.category(char) != "Mn")


def _skill_written(cv_folded: str, label: str) -> bool:
    token = fold(label).strip()
    if not token:
        return False
    if len(token) <= 4:
        return re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", cv_folded) is not None
    return token in cv_folded


def _proof_sentence(cv_text: str, label: str) -> str:
    for line in cv_text.splitlines():
        cleaned = line.strip(" •-\t")
        if cleaned and _skill_written(fold(cleaned), label):
            return cleaned
    return ""


def match_skills(cv_text: str, skills: list[dict], *, lexical_only: bool = False) -> list[dict]:
    if not skills:
        return []
    sentences = split_sentences(cv_text)
    cv_folded = fold(cv_text)
    scores = None
    if not lexical_only:
        sentence_vectors = _encode(sentences)
        skill_vectors = _encode([skill["label"] for skill in skills])
        scores = sentence_vectors @ skill_vectors.T
    results = []
    for index, skill in enumerate(skills):
        written = _skill_written(cv_folded, skill["label"])
        similarity = 0.0
        if scores is not None:
            best = int(scores[:, index].argmax())
            similarity = float(scores[best, index])
        acquired = written or (not lexical_only and similarity >= THRESHOLD and _shares_word(sentences[best] if scores is not None else "", skill["label"]))
        results.append(
            {
                "skill_id": skill["id"],
                "label": skill["label"],
                "required": skill.get("required", True),
                "score": round(similarity if scores is not None else (1.0 if written else 0.0), 3),
                "acquired": acquired,
                "proof": _proof_sentence(cv_text, skill["label"]) if acquired else "",
            }
        )
    return results


def _shares_word(sentence: str, label: str) -> bool:
    words = [word for word in re.findall(r"[a-z]{5,}", fold(label)) if word not in {"informatique", "gestion", "systeme", "donnees"}]
    folded = fold(sentence)
    return any(word in folded for word in words)


_LIST_HEADERS = {
    "langages", "langage", "web", "data science", "ml", "tools", "outils",
    "frameworks", "bibliotheques", "competences",
}
_TECH_TERMS = (
    "intelligence artificielle", "data science", "machine learning", "deep learning",
    "scikit-learn", "random forest", "xgboost", "tensorflow", "pytorch",
    "javascript", "typescript", "laravel", "react", "django", "flask", "spring",
    "python", "java", "c++", "javascript", "php", "html", "css", "js", "mysql", "postgresql", "mongodb", "sql",
    "docker", "kubernetes", "git", "linux", "pandas", "numpy", "polars",
)


def _remember(found: list[str], seen: set[str], label: str) -> None:
    cleaned = re.sub(r"\s+", " ", label).strip(" .•-")
    key = fold(cleaned)
    if not key or key in seen or key in {"etc"} or not 1 < len(cleaned) <= 48:
        return
    seen.add(key)
    found.append(cleaned)


_SECTION_HEADINGS = {
    "competences", "competence", "certificats", "certificat", "langues", "langue",
    "formation", "formations", "etudes", "experiences professionnelles", "experience professionnelle",
    "experiences", "parcours professionnel", "projets realises", "profil", "profil professionnel",
    "centres d'interet", "centres d'interets", "contact",
}
_LANGUAGE_NAMES = (
    "francais", "anglais", "arabe", "amazigh", "espagnol", "allemand", "italien",
    "portugais", "neerlandais", "chinois", "japonais", "russe", "turc", "hindi", "coreen", "suedois",
)
_MONTHS = {
    "janvier": 1, "janv": 1, "jan": 1,
    "fevrier": 2, "fevr": 2, "fev": 2,
    "mars": 3, "mar": 3,
    "avril": 4, "avr": 4,
    "mai": 5,
    "juin": 6, "jun": 6,
    "juillet": 7, "juil": 7, "jul": 7,
    "aout": 8,
    "septembre": 9, "sept": 9, "sep": 9,
    "octobre": 10, "oct": 10,
    "novembre": 11, "nov": 11,
    "decembre": 12, "dec": 12,
}
_MONTH_RE = "janvier|janv|fevrier|fevr|juillet|juil|septembre|sept|octobre|novembre|decembre|aout|mars|avril|juin|mai|jan|fev|avr|jun|jul|sep|oct|nov|dec|mar"


def _heading_key(line: str) -> str:
    return fold(line).strip(" .:-|").replace("’", "'").replace("`", "'")


def _section_body(text: str, names: set[str]) -> str | None:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if _heading_key(line) in names:
            start = index + 1
            break
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if _heading_key(line) in _SECTION_HEADINGS:
            break
        body.append(line)
    return "\n".join(body)


def skills_from_cv(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        cleaned = line.strip(" •-\t")
        header = re.match(r"^([^:]{2,24})\s*:\s*(.+)$", cleaned)
        if not header or fold(header.group(1)) not in _LIST_HEADERS:
            continue
        for part in re.split(r"[,/&]|(\betc\b)", header.group(2), flags=re.IGNORECASE):
            if part:
                _remember(found, seen, part)
    folded = fold(text)
    for term in _TECH_TERMS:
        token = fold(term)
        if any(char in token for char in " +#."):
            present = token in folded
        else:
            present = re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", folded) is not None
        if present:
            _remember(found, seen, term)
    section = _section_body(text, {"competences", "competence"})
    if section:
        for line in section.splitlines():
            cleaned = line.strip(" •-\t|")
            letters = sum(char.isalpha() for char in cleaned)
            if letters >= 4 and letters / max(len(cleaned), 1) >= 0.6:
                _remember(found, seen, cleaned)
    return found


def studies_from_cv(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    markers = ("cycle ingenieur", "classes preparatoires", "cycle preparatoire", "bac")
    extra = ("bts", "dut", "licence", "master", "doctorat", "certification")
    lines = text.splitlines()
    for line in lines:
        cleaned = line.strip(" •-\t")
        folded = fold(cleaned)
        if not any(marker in folded for marker in markers):
            continue
        key = "bac" if re.search(r"\bbac\b", folded) else re.sub(r"[^a-z0-9]+", " ", folded).strip()
        if key in seen or len(cleaned) < 3:
            continue
        seen.add(key)
        found.append(cleaned)
    for index, line in enumerate(lines):
        cleaned = line.strip(" •-\t")
        folded = fold(cleaned)
        if not any(re.search(rf"\b{marker}\b", folded) for marker in extra):
            continue
        key = re.sub(r"[^a-z0-9]+", " ", folded).strip()
        if key in seen or len(cleaned) < 3:
            continue
        seen.add(key)
        found.append(cleaned)
        if index + 1 < len(lines):
            school = lines[index + 1].strip(" •-\t")
            school_key = fold(school)
            if any(token in school_key for token in ("lycee", "ecole", "universite", "institut", "faculte", "ofppt")):
                remembered = re.sub(r"[^a-z0-9]+", " ", school_key).strip()
                if remembered not in seen and len(school) >= 3:
                    seen.add(remembered)
                    found.append(school)
    return found


def languages_from_cv(text: str) -> str:
    section = _section_body(text, {"langues", "langue"})
    folded = fold(section if section is not None else text)
    return ", ".join(name for name in _LANGUAGE_NAMES if re.search(rf"\b{name}\b", folded))


def diploma_from_cv(text: str) -> tuple[str, str]:
    """Only a completed diploma named in the CV counts. Schooling such as Bac or a cycle still in progress does not."""
    labels = {"bac+2": "Bac+2", "bac+3": "Bac+3", "bac+5": "Bac+5", "doctorat": "Doctorat"}
    best = ""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        blob = fold(" ".join(lines[max(0, index - 1) : index + 2]))
        if "en cours" in blob or "etudiant" in blob:
            continue
        line_folded = fold(line)
        found = ""
        if re.search(r"\bdoctorat\b", line_folded):
            found = "doctorat"
        elif re.search(r"\b(master|bac\s*\+\s*5|diplome d'ingenieur|ingenieur diplome)\b", line_folded):
            found = "bac+5"
        elif re.search(r"\b(licence|bac\s*\+\s*3)\b", line_folded):
            found = "bac+3"
        elif re.search(r"\b(dut|bts|bac\s*\+\s*2|diplome)\b", line_folded):
            found = "bac+2"
        if found and DIPLOMA_RANK[found] > DIPLOMA_RANK.get(best, 0):
            best = found
    return best, labels.get(best, "")


def _keep_stage_range(ranges: set[tuple[int, int, int, int]], year_start: int, month_start: int, year_end: int, month_end: int) -> None:
    if not 1 <= month_start <= 12 or not 1 <= month_end <= 12:
        return
    months = (year_end - year_start) * 12 + (month_end - month_start) + 1
    if 1 <= months <= 24:
        ranges.add((year_start, month_start, year_end, month_end))


def experience_years_from_cv(text: str) -> float:
    ranges: set[tuple[int, int, int, int]] = set()
    for match in re.finditer(r"(\d{2})/(\d{4})\s*[-–]\s*(\d{2})/(\d{4})", text):
        window = fold(text[max(0, match.start() - 140) : match.end() + 180])
        if "stage" not in window:
            continue
        month_start, year_start, month_end, year_end = (int(part) for part in match.groups())
        _keep_stage_range(ranges, year_start, month_start, year_end, month_end)
    folded = fold(text)
    written = re.compile(
        rf"\b({_MONTH_RE})\b\.?,?\s*(\d{{4}})\s*[-–—]\s*\b({_MONTH_RE})\b\.?,?\s*(\d{{4}})"
    )
    for match in written.finditer(folded):
        window = folded[max(0, match.start() - 140) : match.end() + 180]
        if "stage" not in window:
            continue
        month_start = _MONTHS[match.group(1)]
        year_start = int(match.group(2))
        month_end = _MONTHS[match.group(3)]
        year_end = int(match.group(4))
        _keep_stage_range(ranges, year_start, month_start, year_end, month_end)
    if not ranges:
        return 0.0
    total = 0
    for year_start, month_start, year_end, month_end in ranges:
        total += (year_end - year_start) * 12 + (month_end - month_start) + 1
    return round(total / 12, 2)


def diploma_points(candidate_level: str, required_level: str) -> float:
    have = DIPLOMA_RANK.get((candidate_level or "").lower(), 0)
    need = DIPLOMA_RANK.get((required_level or "").lower(), 0)
    if need == 0:
        return 15.0
    return 15.0 if have >= need else round(15.0 * have / need, 1)


def language_points(candidate_languages: str, required_languages: str) -> float:
    required = {fold(part.strip()) for part in required_languages.split(",") if part.strip()}
    if not required:
        return 15.0
    owned = {fold(part.strip()) for part in candidate_languages.split(",") if part.strip()}
    return round(15.0 * len(required & owned) / len(required), 1)


def score_profile(matches: list[dict], years: float, years_required: float, diploma: float, languages: float) -> dict:
    required = [item for item in matches if item["required"]] or matches
    acquired = [item for item in required if item["acquired"]]
    missing = [item for item in required if not item["acquired"]]
    skill_points = 50.0 * (len(acquired) / len(required)) if required else 0.0
    if years_required <= 0:
        experience_points = 20.0
    else:
        experience_points = round(20.0 * min(years / years_required, 1), 1)
    total = round(skill_points + experience_points + diploma + languages, 1)
    reasons = [f"{item['label']} écrit dans le CV" for item in acquired[:2]]
    if missing:
        reasons.append(f"{missing[0]['label']} absent du CV")
    return {
        "score": total,
        "skill_points": round(skill_points, 1),
        "experience_points": experience_points,
        "diploma_points": diploma,
        "language_points": languages,
        "acquired": acquired,
        "missing": missing,
        "matched_count": len(acquired),
        "required_count": len(required),
        "reasons": reasons[:3],
    }


def cover_letter(name: str, offer_title: str, diploma: str, years: float, acquired: list[dict]) -> str:
    skills = ", ".join(item["label"] for item in acquired[:4]) or "les éléments présents dans mon CV"
    return (
        f"Madame, Monsieur,\n\n"
        f"Je souhaite postuler au poste de {offer_title}. "
        f"Je m'appelle {name}. J'ai un parcours de {years:g} an(s)"
        f"{' et le diplôme ' + diploma if diploma else ''}. "
        f"Les compétences déjà présentes dans mon CV et utiles pour ce poste sont : {skills}.\n\n"
        f"Je reste disponible pour un entretien.\n\nCordialement,\n{name}"
    )


def five_lines(name: str, domain: str, diploma: str, years: float, skills: list[str], score: float, offer_title: str) -> str:
    skill_line = ", ".join(skills[:5]) or "compétences en cours de lecture"
    return "\n".join(
        [
            f"1. {name}, domaine {domain or 'non précisé'}.",
            f"2. Diplôme : {diploma or 'non renseigné'}.",
            f"3. Expérience : {years:g} an(s).",
            f"4. Compétences : {skill_line}.",
            f"5. Adéquation avec {offer_title} : score {score} sur 100.",
        ]
    )


DOMAIN_TERMS = {
    "Informatique": [
        "python", "java", "javascript", "html", "css", "php", "laravel", "react", "mysql", "sql",
        "docker", "git", "pandas", "numpy", "intelligence artificielle", "data science",
        "machine learning", "deep learning", "programmation", "logiciel", "informatique",
        "developpement web", "cybersecurite", "scikit",
    ],
    "Comptabilité et finance": ["comptabilite", "bilan", "tresorerie", "fiscalite", "audit", "cabinet comptable"],
    "Commerce et vente": ["prospection", "force de vente", "negociation commerciale", "chiffre d'affaires", "vendeur"],
    "Ressources humaines": ["recrutement", "paie", "ressources humaines", "entretien d'embauche", "sirh"],
    "Communication": ["community manager", "relations presse", "redaction web", "campagne publicitaire"],
    "Industrie": ["chaine de production", "maintenance industrielle", "automatisme", "usinage"],
    "Bâtiment": ["maconnerie", "genie civil", "chantier", "beton arme", "conducteur de travaux"],
    "Santé": ["infirmier", "patient", "hopital", "soins infirmiers", "pharmacie"],
    "Enseignement": ["enseignant", "pedagogie", "salle de classe", "programme scolaire"],
    "Transport et logistique": ["logistique", "supply chain", "entrepot", "chauffeur", "transport de marchandises"],
    "Hôtellerie et restauration": [
        "hotel", "hotellerie", "restaurant", "restauration", "cuisinier", "chef de cuisine",
        "receptionniste", "barman", "sommelier", "service en salle",
    ],
    "Agriculture": ["agriculture", "elevage", "recolte", "exploitation agricole", "irrigation"],
}


def rank_domains(text: str) -> list[tuple[str, int]]:
    folded = fold(text)
    scores = []
    for name, terms in DOMAIN_TERMS.items():
        hits = 0
        for term in terms:
            token = fold(term)
            if " " in token:
                found = token in folded
            else:
                found = re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", folded) is not None
            if found:
                hits += 1
        if hits:
            scores.append((name, hits))
    scores.sort(key=lambda item: item[1], reverse=True)
    return scores


def coherence(declared_name: str, detected_name: str, second_name: str | None) -> tuple[str, str]:
    if not detected_name:
        return "partiel", "Le CV ne contient pas assez de compétences reconnues pour confirmer le domaine."
    if detected_name == declared_name:
        return "coherent", f"Le CV correspond au domaine déclaré : {declared_name}."
    if second_name == declared_name:
        return "partiel", f"Le CV couvre {detected_name} et aussi {declared_name}."
    return "incoherent", f"Domaine déclaré : {declared_name}. Le CV parle surtout de {detected_name}."


# Skills a company should be able to require, in the order they are shown.
# Short labels so a word written in the CV, such as Python or SQL, can match.
OFFER_SKILL_CATALOG = {
    "Informatique": [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "HTML", "CSS", "SQL",
        "React", "Angular", "Vue.js", "Laravel", "Django", "Spring", "Node.js", ".NET",
        "MySQL", "PostgreSQL", "MongoDB", "Machine learning", "Deep learning", "Intelligence artificielle",
        "Data science", "Pandas", "TensorFlow", "Scikit-learn", "Docker", "Git", "Linux", "Kubernetes",
        "DevOps", "Cybersécurité",
    ],
    "Comptabilité et finance": [
        "Comptabilité générale", "Comptabilité analytique", "Bilan", "États financiers", "Fiscalité", "TVA",
        "Audit", "Trésorerie", "Contrôle de gestion", "Analyse financière", "Budget", "Paie", "Facturation",
        "IFRS", "Finance d'entreprise",
    ],
    "Commerce et vente": [
        "Techniques de vente", "Prospection", "Négociation commerciale", "Merchandising", "Commerce de détail",
        "Fidélisation", "Argumentaire de vente", "Service client", "Gestion de la relation client",
        "Point de vente", "E-commerce", "Objectifs de vente",
    ],
    "Ressources humaines": [
        "Recrutement", "Entretien d'embauche", "Gestion du personnel", "Droit du travail", "Paie",
        "Contrat de travail", "Formation", "Évaluation du personnel", "Intégration", "Relations sociales",
        "Gestion des talents",
    ],
    "Communication": [
        "Communication", "Rédaction", "Publicité", "Relations publiques", "Médias sociaux", "Graphisme",
        "Journalisme", "Identité visuelle", "Marketing de contenu", "Campagne de communication",
        "Community management",
    ],
    "Industrie": [
        "Maintenance industrielle", "Production", "Automatisation", "Usinage", "Contrôle qualité", "Soudage",
        "Chaîne de production", "Électrotechnique", "Mécanique", "Lean", "Métrologie",
    ],
    "Bâtiment": [
        "Génie civil", "Maçonnerie", "Béton", "Coffrage", "Lecture de plans", "Gros œuvre", "Second œuvre",
        "Chantier", "Plomberie", "Électricité du bâtiment", "Architecture", "Sécurité sur chantier", "Métré",
    ],
    "Santé": [
        "Soins infirmiers", "Anatomie", "Pharmacologie", "Diagnostic", "Premiers soins", "Hygiène hospitalière",
        "Dossier médical", "Radiologie", "Laboratoire", "Soins aux patients",
    ],
    "Enseignement": [
        "Pédagogie", "Didactique", "Programme scolaire", "Évaluation des élèves", "Plan de cours",
        "Gestion de classe", "Méthodes d'enseignement",
    ],
    "Transport et logistique": [
        "Logistique", "Chaîne d'approvisionnement", "Gestion des stocks", "Entrepôt", "Transport de marchandises",
        "Expédition", "Manutention", "Douane", "Livraison", "Planification des itinéraires",
    ],
    "Hôtellerie et restauration": [
        "Cuisine", "Service en salle", "Réception hôtelière", "Hygiène alimentaire", "Œnologie", "Restauration",
        "Hôtellerie", "Accueil", "Bar", "Arts culinaires",
    ],
    "Agriculture": [
        "Agronomie", "Élevage", "Production végétale", "Production animale", "Irrigation", "Récolte",
        "Protection des cultures", "Machinisme agricole", "Sols",
    ],
}
