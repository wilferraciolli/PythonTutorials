from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Create SQLite database file (local)
DATABASE_URL = "sqlite:///./todo.db"

# Create engine (connection pool)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Dependency function for FastAPI
def get_db():
    """Dependency to inject database session into endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
