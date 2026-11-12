from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Domain, User
from app.security import hash_password

DOMAINS = [
    ("Informatique", "informatique", "25,35"),
    ("Comptabilité et finance", "comptabilite-finance", "241,3313,431"),
    ("Commerce et vente", "commerce-vente", "52,3322"),
    ("Ressources humaines", "ressources-humaines", "2423,1212,4416"),
    ("Communication", "communication", "243,1222,264"),
    ("Industrie", "industrie", "72,81,82"),
    ("Bâtiment", "batiment", "71,1323"),
    ("Santé", "sante", "22,32,53"),
    ("Enseignement", "enseignement", "23"),
    ("Transport et logistique", "transport-logistique", "83,432,1324"),
    ("Hôtellerie et restauration", "hotellerie-restauration", "141,51"),
    ("Agriculture", "agriculture", "61,63,921"),
]

USERS = [
    ("candidat1@anapec.test", "Amina Benali", "candidate", "Candidat123", True),
    ("candidat2@anapec.test", "Youssef Amrani", "candidate", "Candidat123", True),
    ("entreprise@anapec.test", "Société Atlas", "entreprise", "Entreprise123", True),
    ("admin@anapec.test", "Mehdi El khou", "admin", "Admin123", True),
    ("bloque@anapec.test", "Compte désactivé", "candidate", "Bloque123", False),
]


def seed_reference(db: Session) -> None:
    if db.scalar(select(Domain.id).limit(1)) is None:
        db.add_all(Domain(name=name, slug=slug, prefixes=prefixes) for name, slug, prefixes in DOMAINS)
    if db.scalar(select(User.id).limit(1)) is None:
        db.add_all(
            User(
                email=email,
                full_name=name,
                role=role,
                password_hash=hash_password(password),
                is_active=active,
            )
            for email, name, role, password, active in USERS
        )
    db.commit()
