import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinel:sentinel_password@localhost:5432/sentinel_db")
backend_dir = os.path.dirname(os.path.abspath(__file__))
sqlite_path = os.path.join(backend_dir, "sentinel.db").replace("\\", "/")
FALLBACK_SQLITE_URL = f"sqlite:///{sqlite_path}"

# Resilient Engine Setup: Attempt PostgreSQL first, fall back to SQLite if Postgres is unavailable
try:
    if "postgresql" in DATABASE_URL:
        # Test connection with a fast timeout
        test_engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        print(f"[DB] Connected successfully to primary PostgreSQL database: {DATABASE_URL.split('@')[-1]}")
    else:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
except Exception as e:
    print(f"[DB Warning] Could not connect to PostgreSQL ({e}). Falling back to local SQLite: {FALLBACK_SQLITE_URL}")
    DATABASE_URL = FALLBACK_SQLITE_URL
    engine = create_engine(FALLBACK_SQLITE_URL, connect_args={"check_same_thread": False})

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
