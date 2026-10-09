
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Store the database in a local SQLite file.
DATABASE_URL = "sqlite:///./certificates.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create database sessions for API requests.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for our database models.
Base = declarative_base()


# Provide a database session and close it after use.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
