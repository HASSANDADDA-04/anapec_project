from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(180))
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), index=True)
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domains.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["CandidateProfile | None"] = relationship(back_populates="user", uselist=False)
    offers: Mapped[list["Offer"]] = relationship(back_populates="employer")


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    prefixes: Mapped[str] = mapped_column(String(200))


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(300), index=True)
    skill_type: Mapped[str] = mapped_column(String(80), default="")


class Occupation(Base):
    __tablename__ = "occupations"

    id: Mapped[int] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(300))
    isco_group: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domains.id"))


class OccupationSkill(Base):
    __tablename__ = "occupation_skills"
    __table_args__ = (UniqueConstraint("occupation_id", "skill_id", "relation_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    occupation_id: Mapped[int] = mapped_column(ForeignKey("occupations.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(20))


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domains.id"))
    city: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    diploma_title: Mapped[str] = mapped_column(String(200), default="")
    diploma_level: Mapped[str] = mapped_column(String(40), default="")
    years_experience: Mapped[float] = mapped_column(Float, default=0)
    languages: Mapped[str] = mapped_column(String(200), default="")
    birth_date: Mapped[str] = mapped_column(String(10), default="")
    cv_filename: Mapped[str] = mapped_column(String(260), default="")
    cv_path: Mapped[str] = mapped_column(String(400), default="")
    cv_text: Mapped[str] = mapped_column(Text, default="")
    coherence: Mapped[str] = mapped_column(String(20), default="")
    coherence_note: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="profile")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    diploma_level: Mapped[str] = mapped_column(String(40), default="")
    years_required: Mapped[float] = mapped_column(Float, default=0)
    languages: Mapped[str] = mapped_column(String(400), default="")
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domains.id"))
    status: Mapped[str] = mapped_column(String(20), default="online")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employer: Mapped[User] = relationship(back_populates="offers")
    skills: Mapped[list["OfferSkill"]] = relationship(back_populates="offer", cascade="all, delete-orphan")


class OfferSkill(Base):
    __tablename__ = "offer_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    offer: Mapped[Offer] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship()


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "offer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    letter: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="envoyee")
    score: Mapped[float | None] = mapped_column(Float)
    reasons: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    acquired: Mapped[str] = mapped_column(Text, default="")
    missing: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped[User] = relationship(foreign_keys=[candidate_id])
    offer: Mapped[Offer] = relationship()


class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"))
    kind: Mapped[str] = mapped_column(String(20), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    domain_id: Mapped[int | None] = mapped_column(ForeignKey("domains.id"))
    duration: Mapped[str] = mapped_column(String(80), default="")
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"))
    level: Mapped[str] = mapped_column(String(40), default="")

    skill: Mapped[Skill | None] = relationship()
