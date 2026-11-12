from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import User
from app.routers.api import router
from app.security import hash_password, verify_password
from app.seed import seed_reference

app = FastAPI(title="ANAPEC")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:80",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    if inspector.has_table("candidate_profiles"):
        columns = {column["name"] for column in inspector.get_columns("candidate_profiles")}
        if "birth_date" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE candidate_profiles ADD COLUMN birth_date VARCHAR(10) DEFAULT ''"))
    if inspector.has_table("users"):
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "domain_id" not in user_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN domain_id INTEGER REFERENCES domains(id)"))
    if inspector.has_table("offers"):
        offer_columns = {column["name"] for column in inspector.get_columns("offers")}
        languages = next((column for column in inspector.get_columns("offers") if column["name"] == "languages"), None)
        if languages and languages.get("type") is not None and "200" in str(languages["type"]):
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE offers ALTER COLUMN languages TYPE VARCHAR(400)"))
    with engine.begin() as connection:
        connection.execute(text("UPDATE users SET role = 'entreprise' WHERE role = 'employer'"))
        connection.execute(text(
            "UPDATE users AS company SET domain_id = ("
            "SELECT offer.domain_id FROM offers AS offer "
            "WHERE offer.employer_id = company.id AND offer.domain_id IS NOT NULL "
            "ORDER BY offer.id LIMIT 1) "
            "WHERE company.role = 'entreprise' AND company.domain_id IS NULL"
        ))
        connection.execute(text(
            "UPDATE users SET email = 'entreprise@anapec.test' "
            "WHERE email = 'employeur@anapec.test' "
            "AND NOT EXISTS (SELECT 1 FROM users AS other WHERE other.email = 'entreprise@anapec.test')"
        ))
    db = SessionLocal()
    try:
        seed_reference(db)
        company = db.scalar(select(User).where(User.email == "entreprise@anapec.test"))
        if company is not None and verify_password("Employeur123", company.password_hash):
            company.password_hash = hash_password("Entreprise123")
            company.role = "entreprise"
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
