import os
from sqlalchemy import create_engine, inspect, text
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
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False, "timeout": 30},
            pool_size=50,
            max_overflow=50,
            pool_timeout=30,
            pool_pre_ping=True,
        )
except Exception as e:
    print(f"[DB Warning] Could not connect to PostgreSQL ({e}). Falling back to local SQLite: {FALLBACK_SQLITE_URL}")
    DATABASE_URL = FALLBACK_SQLITE_URL
    engine = create_engine(
        FALLBACK_SQLITE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_size=50,
        max_overflow=50,
        pool_timeout=30,
        pool_pre_ping=True,
    )


def ensure_schema_compatibility(target_engine):
    """
    Inspects existing database schema and applies missing columns cleanly:
    - Inspects existing columns first
    - Never uses SQLite 'ADD COLUMN IF NOT EXISTS' (invalid SQLite syntax)
    - Adds only truly missing columns via standard ALTER TABLE
    """
    try:
        inspector = inspect(target_engine)
        existing_tables = inspector.get_table_names()

        if "cameras" in existing_tables:
            existing_cols = {col["name"] for col in inspector.get_columns("cameras")}
            expected_camera_cols = [
                ("onvif_host", "VARCHAR(255)"),
                ("onvif_port", "INTEGER"),
                ("onvif_username", "VARCHAR(255)"),
                ("onvif_password", "VARCHAR(255)"),
            ]
            with target_engine.connect() as conn:
                for col_name, col_type in expected_camera_cols:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE cameras ADD COLUMN {col_name} {col_type}"))
                conn.commit()

        if "plates" in existing_tables:
            existing_cols = {col["name"] for col in inspector.get_columns("plates")}
            if "normalized_plate" not in existing_cols:
                with target_engine.connect() as conn:
                    conn.execute(text("ALTER TABLE plates ADD COLUMN normalized_plate VARCHAR(30)"))
                    conn.commit()

        if "cameras" in existing_tables:
            with target_engine.connect() as conn:
                try:
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_cameras_name ON cameras(name)"))
                    conn.commit()
                except Exception:
                    pass

        if "users" in existing_tables:
            existing_cols = {col["name"] for col in inspector.get_columns("users")}
            if "password_hash" not in existing_cols:
                with target_engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                    conn.commit()

    except Exception as err:
        print(f"[DB Migration Warning] Schema compatibility check encountered an issue: {err}")


# Run migration check immediately on engine setup
ensure_schema_compatibility(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

