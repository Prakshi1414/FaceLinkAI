# app/db/database.py
# ─────────────────────────────────────────────────────────────────────────────
# SQLAlchemy engine, session factory, and Base model.
# All ORM models inherit from Base.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # drop stale connections automatically
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    echo=(settings.APP_ENV == "development"),
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Declarative Base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()