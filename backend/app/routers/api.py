import json
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.database import get_db
from app.models import (
    Application,
    CandidateProfile,
    Domain,
    Notice,
    Offer,
    OfferSkill,
    Occupation,
    OccupationSkill,
    Skill,
    Training,
    User,
)
from app.security import create_token, get_current_user, hash_password, require_role, verify_password
from app.services.extract import extract_text
from app.services.matching import (
    coherence,
    cover_letter,
    diploma_from_cv,
    diploma_points,
    experience_years_from_cv,
    five_lines,
    fold,
    language_points,
    languages_from_cv,
    match_skills,
    OFFER_SKILL_CATALOG,
    rank_domains,
    score_profile,
    skills_from_cv,
    studies_from_cv,
)

router = APIRouter()


class LoginIn(BaseModel):
    email: str
    password: str


class RegisterIn(BaseModel):
    full_name: str
    email: str
    password: str
    password_confirm: str
    role: str
    birth_date: str = ""
    domain_id: int | None = None


class ProfileIn(BaseModel):
    domain_id: int | None = None
    city: str = ""
    phone: str = ""
    diploma_title: str = ""
    diploma_level: str = ""
    years_experience: float = 0
    languages: str = ""
    birth_date: str = ""


class OfferIn(BaseModel):
    title: str
    city: str = ""
    description: str = ""
    diploma_level: str = ""
    years_required: float = 0
    languages: str = ""
    domain_id: int | None = None
    skill_ids: list[int] = []
    status: str = "online"


class ApplyIn(BaseModel):
    letter: str = ""


class DecisionIn(BaseModel):
    status: str


class UserStatusIn(BaseModel):
    is_active: bool


class AdminUserIn(BaseModel):
    full_name: str
    email: str
    password: str = ""
    role: str
    is_active: bool = True


def _user_out(user: User, db: Session | None = None) -> dict:
    data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
    }
    if db is not None and user.role == "entreprise":
        data["domain_id"] = user.domain_id
        data["domain_name"] = _domain_name(db, user.domain_id)
    return data


def _profile(db: Session, user: User) -> CandidateProfile:
    profile = db.get(CandidateProfile, user.id)
    if profile is None:
        profile = CandidateProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _domain_name(db: Session, domain_id: int | None) -> str:
    if domain_id is None:
        return ""
    domain = db.get(Domain, domain_id)
    return domain.name if domain else ""


def _suggest_trainings(db: Session, missing: list[dict], limit: int = 3) -> list[dict]:
    found = []
    for item in missing:
        training = db.scalar(select(Training).where(Training.skill_id == item["skill_id"]))
        if training:
            found.append(
                {"title": training.title, "duration": training.duration, "skill": item["label"], "level": training.level}
            )
        else:
            found.append(
                {
                    "title": f"Formation {item['label']}",
                    "duration": "20 heures",
                    "skill": item["label"],
                    "level": "intermédiaire",
                }
            )
        if len(found) >= limit:
            break
    return found


def _detect_domain(db: Session, cv_text: str, declared_id: int | None) -> tuple[str, str]:
    declared = _domain_name(db, declared_id)
    ranked = rank_domains(cv_text)
    detected = ranked[0][0] if ranked else ""
    second = ranked[1][0] if len(ranked) > 1 else None
    return coherence(declared, detected, second)


def _birth_date(value: str) -> str:
    try:
        born = date.fromisoformat((value or "").strip())
    except ValueError:
        raise HTTPException(status_code=400, detail="Indiquez une date de naissance valide")
    today = date.today()
    if born > today or born.year < 1940:
        raise HTTPException(status_code=400, detail="La date de naissance n'est pas valide")
    return born.isoformat()


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou mot de passe incorrect")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Ce compte est désactivé")
    return {"token": create_token(user), "user": _user_out(user, db)}


@router.post("/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    role = body.role.strip().lower()
    if body.password != body.password_confirm:
        raise HTTPException(status_code=400, detail="Les deux mots de passe ne correspondent pas")
    if role not in {"candidate", "entreprise"}:
        raise HTTPException(status_code=400, detail="Choisissez candidat ou entreprise")
    email = body.email.strip().lower()
    name = body.full_name.strip()
    if len(name) < 2 or "@" not in email or len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Indiquez un nom, un e-mail et un mot de passe d'au moins 6 caractères")
    birth = _birth_date(body.birth_date) if role == "candidate" else ""
    domain_id = None
    if role == "entreprise":
        domain = db.get(Domain, body.domain_id) if body.domain_id else None
        if domain is None:
            raise HTTPException(status_code=400, detail="Choisissez le domaine de l'entreprise")
        domain_id = domain.id
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Cet e-mail est déjà utilisé")
    user = User(
        email=email,
        full_name=name,
        role=role,
        domain_id=domain_id,
        password_hash=hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if role == "candidate":
        db.add(CandidateProfile(user_id=user.id, birth_date=birth))
        db.commit()
    return {"token": create_token(user), "user": _user_out(user, db)}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _user_out(user, db)


@router.get("/domains")
def domains(db: Session = Depends(get_db)):
    rows = db.scalars(select(Domain).order_by(Domain.name)).all()
    return [{"id": row.id, "name": row.name, "slug": row.slug} for row in rows]


def _catalog_skills(db: Session, domain_name: str) -> list[Skill]:
    labels = OFFER_SKILL_CATALOG.get(domain_name) or []
    found = []
    created = False
    for label in labels:
        skill = db.scalar(select(Skill).where(Skill.label == label))
        if skill is None:
            slug = fold(label).replace(" ", "-")[:80]
            skill = Skill(uri=f"anapec:{slug}", label=label, skill_type="catalogue")
            db.add(skill)
            created = True
        found.append(skill)
    if created:
        db.commit()
        for skill in found:
            db.refresh(skill)
    return found


@router.get("/skills")
def skills(q: str = "", domain_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    domain = db.get(Domain, domain_id) if domain_id else None
    catalog = _catalog_skills(db, domain.name) if domain else []
    if domain and not q.strip():
        return [{"id": skill.id, "label": skill.label} for skill in catalog]
    query = select(Skill)
    if domain_id:
        query = (
            query.join(OccupationSkill, OccupationSkill.skill_id == Skill.id)
            .join(Occupation, Occupation.id == OccupationSkill.occupation_id)
            .where(Occupation.domain_id == domain_id)
        )
    if q.strip():
        query = query.where(Skill.label.ilike(f"%{q.strip()}%"))
    rows = db.scalars(query.distinct().order_by(Skill.label).limit(40)).all()
    seen = {row.id for row in rows}
    extra = [skill for skill in catalog if skill.id not in seen and (not q.strip() or q.strip().lower() in skill.label.lower())]
    return [{"id": skill.id, "label": skill.label} for skill in [*extra, *rows]]


@router.get("/profile")
def get_profile(user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    profile = _profile(db, user)
    _refresh_coherence(db, profile)
    return {
        "user": _user_out(user),
        "domain_id": profile.domain_id,
        "domain_name": _domain_name(db, profile.domain_id),
        "city": profile.city,
        "phone": profile.phone,
        "diploma_title": profile.diploma_title,
        "diploma_level": profile.diploma_level,
        "years_experience": profile.years_experience,
        "languages": profile.languages,
        "birth_date": profile.birth_date,
        "cv_filename": profile.cv_filename,
        "cv_text": profile.cv_text,
        "coherence": profile.coherence,
        "coherence_note": profile.coherence_note,
    }


@router.put("/profile")
def update_profile(body: ProfileIn, user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    profile = _profile(db, user)
    for field in ("domain_id", "city", "phone"):
        setattr(profile, field, getattr(body, field))
    if body.birth_date:
        profile.birth_date = _birth_date(body.birth_date)
    if profile.cv_text and profile.domain_id:
        status, note = _detect_domain(db, profile.cv_text, profile.domain_id)
        profile.coherence = status
        profile.coherence_note = note
    db.commit()
    return {"ok": True, "coherence": profile.coherence, "coherence_note": profile.coherence_note}


class AnalyzeProfileIn(BaseModel):
    domain_id: int | None = None


@router.post("/profile/analyze")
def analyze_profile(body: AnalyzeProfileIn, user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    profile = _profile(db, user)
    if body.domain_id:
        profile.domain_id = body.domain_id
    if not profile.cv_path or not Path(profile.cv_path).is_file() or not (profile.cv_text or "").strip():
        raise HTTPException(status_code=400, detail="Déposez un CV dans Mon profil avant de l'analyser")
    if not profile.domain_id:
        raise HTTPException(status_code=400, detail="Choisissez un domaine avant d'analyser le CV")
    status, note = _detect_domain(db, profile.cv_text, profile.domain_id)
    profile.coherence = status
    profile.coherence_note = note
    db.commit()
    months = int(round(experience_years_from_cv(profile.cv_text) * 12))
    _, diploma = diploma_from_cv(profile.cv_text)
    return {
        "coherence": status,
        "coherence_note": note,
        "skills": skills_from_cv(profile.cv_text),
        "languages": languages_from_cv(profile.cv_text),
        "experience_months": months,
        "diploma": diploma,
        "studies": studies_from_cv(profile.cv_text),
    }


@router.post("/cv")
def upload_cv(
    file: UploadFile = File(...),
    user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Déposez un PDF ou un fichier Word .docx")
    folder = Path(settings.upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{user.id}{suffix}"
    target.write_bytes(file.file.read())
    try:
        text = extract_text(target)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    profile = _profile(db, user)
    profile.cv_filename = file.filename or target.name
    profile.cv_path = str(target)
    profile.cv_text = text
    if profile.domain_id:
        status, note = _detect_domain(db, text, profile.domain_id)
        profile.coherence = status
        profile.coherence_note = note
    db.commit()
    return {
        "filename": profile.cv_filename,
        "text": text,
        "coherence": profile.coherence,
        "coherence_note": profile.coherence_note,
    }


@router.get("/offers")
def list_offers(
    q: str = "",
    city: str = "",
    domain_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Offer).options(selectinload(Offer.skills).selectinload(OfferSkill.skill))
    if user.role == "entreprise":
        query = query.where(Offer.employer_id == user.id)
    elif user.role == "candidate":
        query = query.where(Offer.status == "online")
    if city.strip():
        query = query.where(Offer.city == city.strip())
    if domain_id:
        query = query.where(Offer.domain_id == domain_id)
    rows = db.scalars(query.order_by(Offer.created_at.desc())).all()
    needle = q.strip().lower()
    if needle:
        rows = [
            row for row in rows
            if needle in f"{row.title} {row.description} {' '.join(item.skill.label for item in row.skills)}".lower()
        ]
    applied_ids = set()
    if user.role == "candidate":
        applied_ids = set(db.scalars(select(Application.offer_id).where(Application.candidate_id == user.id)))
    return [_offer_out(db, row, row.id in applied_ids) for row in rows]


def _offer_out(db: Session, offer: Offer, applied: bool = False) -> dict:
    return {
        "id": offer.id,
        "title": offer.title,
        "city": offer.city,
        "description": offer.description,
        "diploma_level": offer.diploma_level,
        "years_required": offer.years_required,
        "languages": offer.languages,
        "domain_id": offer.domain_id,
        "domain_name": _domain_name(db, offer.domain_id),
        "status": offer.status,
        "entreprise_name": offer.employer.full_name if offer.employer else "",
        "skills": [{"id": item.skill_id, "label": item.skill.label, "required": item.required} for item in offer.skills],
        "applied": applied,
    }


@router.post("/offers")
def create_offer(body: OfferIn, user: User = Depends(require_role("entreprise")), db: Session = Depends(get_db)):
    if not user.domain_id:
        raise HTTPException(status_code=400, detail="Le domaine de l'entreprise est choisi à l'inscription")
    offer = Offer(
        employer_id=user.id,
        title=body.title,
        city=body.city,
        description=body.description,
        diploma_level=body.diploma_level,
        years_required=body.years_required,
        languages=body.languages,
        domain_id=user.domain_id,
        status=body.status if body.status in {"online", "withdrawn"} else "online",
    )
    db.add(offer)
    db.flush()
    for skill_id in body.skill_ids:
        db.add(OfferSkill(offer_id=offer.id, skill_id=skill_id, required=True))
    db.commit()
    db.refresh(offer)
    return {"id": offer.id}


@router.patch("/offers/{offer_id}")
def update_offer_status(
    offer_id: int,
    body: UserStatusIn,
    user: User = Depends(require_role("entreprise")),
    db: Session = Depends(get_db),
):
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    if offer.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    offer.status = "online" if body.is_active else "withdrawn"
    db.commit()
    return {"status": offer.status}


@router.put("/offers/{offer_id}")
def update_offer(offer_id: int, body: OfferIn, user: User = Depends(require_role("entreprise")), db: Session = Depends(get_db)):
    offer = db.scalar(select(Offer).options(selectinload(Offer.skills)).where(Offer.id == offer_id))
    if offer is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    if offer.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    title = body.title.strip()
    if len(title) < 2:
        raise HTTPException(status_code=400, detail="Indiquez l'intitulé de l'offre")
    offer.title = title
    offer.city = body.city.strip()
    offer.description = body.description
    offer.diploma_level = body.diploma_level
    offer.years_required = body.years_required
    offer.languages = body.languages
    db.execute(delete(OfferSkill).where(OfferSkill.offer_id == offer.id))
    for skill_id in body.skill_ids:
        db.add(OfferSkill(offer_id=offer.id, skill_id=skill_id, required=True))
    db.commit()
    offer = db.scalar(select(Offer).options(selectinload(Offer.skills).selectinload(OfferSkill.skill)).where(Offer.id == offer.id))
    return _offer_out(db, offer)


def _require_cv(profile: CandidateProfile) -> None:
    has_file = bool(profile.cv_path) and Path(profile.cv_path).is_file()
    has_text = bool((profile.cv_text or "").strip())
    if not has_file or not has_text:
        raise HTTPException(status_code=400, detail="Déposez un CV avant de postuler")


def _refresh_coherence(db: Session, profile: CandidateProfile) -> tuple[str, str]:
    if not profile.domain_id or not (profile.cv_text or "").strip():
        return profile.coherence or "", profile.coherence_note or ""
    status, note = _detect_domain(db, profile.cv_text, profile.domain_id)
    if profile.coherence != status or profile.coherence_note != note:
        profile.coherence = status
        profile.coherence_note = note
        db.commit()
    return status, note


def _block_if_incoherent(db: Session, profile: CandidateProfile) -> None:
    status, note = _refresh_coherence(db, profile)
    if status == "incoherent":
        raise HTTPException(
            status_code=400,
            detail=f"Votre domaine ne correspond pas à votre CV. Vous ne pouvez pas postuler. {note}",
        )


def _build_analysis(db: Session, profile: CandidateProfile, offer: Offer, user: User) -> dict:
    _require_cv(profile)
    skills = [{"id": item.skill_id, "label": item.skill.label, "required": item.required} for item in offer.skills]
    if not skills and offer.domain_id:
        skill_rows = db.scalars(
            select(Skill)
            .join(OccupationSkill, OccupationSkill.skill_id == Skill.id)
            .join(Occupation, Occupation.id == OccupationSkill.occupation_id)
            .where(Occupation.domain_id == offer.domain_id, OccupationSkill.relation_type == "essential")
            .limit(12)
        ).all()
        skills = [{"id": skill.id, "label": skill.label, "required": True} for skill in skill_rows]
    matches = match_skills(profile.cv_text, skills, lexical_only=True)
    cv_level, cv_diploma = diploma_from_cv(profile.cv_text)
    cv_years = experience_years_from_cv(profile.cv_text)
    cv_languages = languages_from_cv(profile.cv_text)
    years = cv_years
    spoken = cv_languages
    diploma = diploma_points(cv_level, offer.diploma_level)
    languages = language_points(spoken, offer.languages)
    result = score_profile(matches, years, offer.years_required or 0, diploma, languages)
    if cv_diploma:
        result["reasons"].append(f"{cv_diploma} lu dans le CV, {offer.diploma_level or 'niveau non précisé'} demandé")
    elif offer.diploma_level:
        result["reasons"].append("Aucun diplôme obtenu lu dans le CV")
    if offer.years_required:
        months = int(round(years * 12))
        result["reasons"].append(f"{months} mois lus dans le CV, {offer.years_required:g} an(s) demandé(s)")
    result["reasons"] = result["reasons"][:4]
    trainings = _suggest_trainings(db, result["missing"])
    letter = cover_letter(user.full_name, offer.title, cv_diploma, years, result["acquired"])
    summary = five_lines(
        user.full_name,
        _domain_name(db, profile.domain_id),
        cv_diploma,
        years,
        [item["label"] for item in result["acquired"]],
        result["score"],
        offer.title,
    )
    return {**result, "trainings": trainings, "letter": letter, "summary": summary}


@router.post("/offers/{offer_id}/analyze")
def analyze_offer(offer_id: int, user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    offer = db.scalar(select(Offer).options(selectinload(Offer.skills).selectinload(OfferSkill.skill)).where(Offer.id == offer_id))
    if offer is None or offer.status != "online":
        raise HTTPException(status_code=404, detail="Offre introuvable")
    existing = db.scalar(select(Application).where(Application.candidate_id == user.id, Application.offer_id == offer.id))
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà postulé à cette offre")
    profile = _profile(db, user)
    _block_if_incoherent(db, profile)
    return _build_analysis(db, profile, offer, user)


@router.post("/offers/{offer_id}/apply")
def apply(offer_id: int, body: ApplyIn, user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    offer = db.scalar(select(Offer).options(selectinload(Offer.skills).selectinload(OfferSkill.skill)).where(Offer.id == offer_id))
    if offer is None or offer.status != "online":
        raise HTTPException(status_code=404, detail="Offre introuvable")
    existing = db.scalar(select(Application).where(Application.candidate_id == user.id, Application.offer_id == offer.id))
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà postulé à cette offre")
    profile = _profile(db, user)
    _block_if_incoherent(db, profile)
    analysis = _build_analysis(db, profile, offer, user)
    application = Application(
        candidate_id=user.id,
        offer_id=offer.id,
        letter=body.letter or analysis["letter"],
        score=analysis["score"],
        reasons=json.dumps(analysis["reasons"], ensure_ascii=False),
        summary=analysis["summary"],
        acquired=json.dumps(analysis["acquired"], ensure_ascii=False),
        missing=json.dumps(
            {"skills": analysis["missing"], "trainings": analysis["trainings"]},
            ensure_ascii=False,
        ),
    )
    db.add(application)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Vous avez déjà postulé à cette offre")
    return {"id": application.id, "score": analysis["score"]}


def _application_out(row: Application, db: Session) -> dict:
    reasons = json.loads(row.reasons or "[]")
    missing = json.loads(row.missing or "{}")
    acquired = json.loads(row.acquired or "[]")
    profile = db.get(CandidateProfile, row.candidate_id)
    return {
        "id": row.id,
        "offer_id": row.offer_id,
        "offer_title": row.offer.title if row.offer else "",
        "candidate_name": row.candidate.full_name if row.candidate else "",
        "status": row.status,
        "score": row.score,
        "reasons": reasons,
        "summary": row.summary,
        "letter": row.letter,
        "acquired": acquired,
        "missing": missing.get("skills", []),
        "trainings": missing.get("trainings", []),
        "cv_filename": profile.cv_filename if profile else "",
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


@router.get("/applications")
def my_applications(user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Application)
        .options(selectinload(Application.offer), selectinload(Application.candidate))
        .where(Application.candidate_id == user.id)
        .order_by(Application.created_at.desc())
    ).all()
    return [_application_out(row, db) for row in rows]


@router.get("/offers/{offer_id}/applications")
def offer_applications(offer_id: int, user: User = Depends(require_role("entreprise", "admin")), db: Session = Depends(get_db)):
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    if user.role == "entreprise" and offer.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    rows = db.scalars(
        select(Application)
        .options(selectinload(Application.offer), selectinload(Application.candidate))
        .where(Application.offer_id == offer_id)
        .order_by(Application.score.desc().nullslast())
    ).all()
    return [_application_out(row, db) for row in rows]


@router.patch("/applications/{application_id}")
def decide_application(
    application_id: int,
    body: DecisionIn,
    user: User = Depends(require_role("entreprise", "admin")),
    db: Session = Depends(get_db),
):
    status = body.status.strip().lower()
    if status not in {"acceptee", "refusee"}:
        raise HTTPException(status_code=400, detail="Choisissez accepter ou refuser")
    row = db.scalar(
        select(Application)
        .options(selectinload(Application.offer), selectinload(Application.candidate))
        .where(Application.id == application_id)
    )
    if row is None or row.offer is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    if user.role == "entreprise" and row.offer.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    changed = row.status != status
    row.status = status
    if changed:
        title = row.offer.title
        decision = "a retenu" if status == "acceptee" else "n'a pas retenu"
        db.add(Notice(
            user_id=row.candidate_id,
            application_id=row.id,
            kind=status,
            message=f"L'entreprise {decision} votre candidature pour « {title} ».",
        ))
    db.commit()
    return _application_out(row, db)


@router.get("/notices")
def my_notices(user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Notice).where(Notice.user_id == user.id, Notice.read.is_(False)).order_by(Notice.created_at.desc())
    ).all()
    return [
        {"id": row.id, "kind": row.kind, "message": row.message, "read": row.read, "created_at": row.created_at.isoformat() if row.created_at else ""}
        for row in rows
    ]


@router.post("/notices/{notice_id}/read")
def read_notice(notice_id: int, user: User = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    row = db.get(Notice, notice_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Message introuvable")
    row.read = True
    db.commit()
    return {"ok": True}


@router.get("/applications/{application_id}/cv")
def application_cv(application_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.scalar(
        select(Application).options(selectinload(Application.offer)).where(Application.id == application_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    allowed = user.role == "admin" or row.candidate_id == user.id
    if user.role == "entreprise":
        allowed = row.offer is not None and row.offer.employer_id == user.id
    if not allowed:
        raise HTTPException(status_code=403, detail="Accès refusé")
    profile = db.get(CandidateProfile, row.candidate_id)
    if profile is None or not profile.cv_path or not Path(profile.cv_path).is_file():
        raise HTTPException(status_code=404, detail="Fichier CV introuvable")
    return FileResponse(profile.cv_path, filename=profile.cv_filename or Path(profile.cv_path).name)


@router.get("/admin/users")
def admin_users(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    rows = db.scalars(select(User).order_by(User.role, User.full_name)).all()
    return [_user_out(row) for row in rows]


def _checked_role(role: str) -> str:
    value = role.strip().lower()
    if value not in {"candidate", "entreprise", "admin"}:
        raise HTTPException(status_code=400, detail="Choisissez candidat, entreprise ou administrateur")
    return value


def _remove_user(db: Session, user: User) -> None:
    offer_ids = list(db.scalars(select(Offer.id).where(Offer.employer_id == user.id)))
    filters = [Application.candidate_id == user.id]
    if offer_ids:
        filters.append(Application.offer_id.in_(offer_ids))
        db.execute(delete(OfferSkill).where(OfferSkill.offer_id.in_(offer_ids)))
    db.execute(delete(Application).where(or_(*filters)))
    if offer_ids:
        db.execute(delete(Offer).where(Offer.id.in_(offer_ids)))
    profile = db.get(CandidateProfile, user.id)
    if profile is not None and profile.cv_path:
        Path(profile.cv_path).unlink(missing_ok=True)
    db.execute(delete(CandidateProfile).where(CandidateProfile.user_id == user.id))
    db.delete(user)


@router.post("/admin/users")
def admin_create_user(body: AdminUserIn, _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    role = _checked_role(body.role)
    email = body.email.strip().lower()
    name = body.full_name.strip()
    if len(name) < 2 or "@" not in email or len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Indiquez un nom, un e-mail et un mot de passe d'au moins 6 caractères")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Cet e-mail est déjà utilisé")
    user = User(email=email, full_name=name, role=role, password_hash=hash_password(body.password), is_active=body.is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    if role == "candidate":
        db.add(CandidateProfile(user_id=user.id))
        db.commit()
    return _user_out(user)


@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    _remove_user(db, user)
    db.commit()
    return {"ok": True}


@router.get("/admin/alerts")
def admin_alerts(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(CandidateProfile).where(CandidateProfile.coherence.in_(["partiel", "incoherent"]))
    ).all()
    result = []
    for profile in rows:
        user = db.get(User, profile.user_id)
        result.append(
            {
                "user_id": profile.user_id,
                "name": user.full_name if user else "",
                "email": user.email if user else "",
                "domain": _domain_name(db, profile.domain_id),
                "coherence": profile.coherence,
                "note": profile.coherence_note,
            }
        )
    return result


@router.get("/admin/dashboard")
def admin_dashboard(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    offer_counts = db.execute(
        select(Domain.name, func.count(Offer.id))
        .join(Offer, Offer.domain_id == Domain.id)
        .where(Offer.status == "online")
        .group_by(Domain.name)
        .order_by(func.count(Offer.id).desc())
    ).all()
    weak_offers = []
    offers = db.scalars(select(Offer).where(Offer.status == "online")).all()
    for offer in offers:
        best = db.scalar(select(func.max(Application.score)).where(Application.offer_id == offer.id))
        if best is None or best < 60:
            weak_offers.append({"id": offer.id, "title": offer.title, "best_score": best})
    alerts = db.scalar(
        select(func.count()).select_from(CandidateProfile).where(CandidateProfile.coherence == "incoherent")
    )
    missing_counts: dict[str, int] = {}
    for raw in db.scalars(select(Application.missing)).all():
        payload = json.loads(raw or "{}")
        for skill in payload.get("skills", []):
            label = skill.get("label") or ""
            if label:
                missing_counts[label] = missing_counts.get(label, 0) + 1
    often_missing = [
        {"label": label, "count": count}
        for label, count in sorted(missing_counts.items(), key=lambda item: item[1], reverse=True)[:8]
    ]
    return {
        "candidates": db.scalar(select(func.count()).select_from(User).where(User.role == "candidate")),
        "entreprises": db.scalar(select(func.count()).select_from(User).where(User.role == "entreprise")),
        "offers": db.scalar(select(func.count()).select_from(Offer).where(Offer.status == "online")),
        "applications": db.scalar(select(func.count()).select_from(Application)),
        "incoherent_profiles": alerts or 0,
        "demanded_domains": [{"name": name, "offers": count} for name, count in offer_counts],
        "offers_without_fit": weak_offers,
        "often_missing": often_missing,
    }
