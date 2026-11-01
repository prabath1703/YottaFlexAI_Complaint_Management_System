from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'complaint_management.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_database():
    with engine.begin() as connection:
        columns = connection.execute(
            text("PRAGMA table_info(sla_clocks)")
        ).fetchall()

        existing_columns = {column[1] for column in columns}

        if "paused_at" not in existing_columns:
            connection.execute(
                text("ALTER TABLE sla_clocks ADD COLUMN paused_at DATETIME")
            )

        if "breached_at" not in existing_columns:
            connection.execute(
                text("ALTER TABLE sla_clocks ADD COLUMN breached_at DATETIME")
            )


def create_tables():
    Base.metadata.create_all(bind=engine)
    migrate_database()