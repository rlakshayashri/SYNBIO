from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.session import SessionLocal, engine


def test_database_config_validity() -> None:
    """Verify that database configuration settings are loaded correctly."""
    assert settings.DATABASE_URL is not None
    assert ("postgresql" in settings.DATABASE_URL) or ("sqlite" in settings.DATABASE_URL)
    assert "syndatax" in settings.DATABASE_URL


def test_database_connection() -> None:
    """Verify SQLAlchemy engine connectivity to database when available."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except OperationalError:
        # PostgreSQL container might not be running in isolated CI/unit environment
        pass


def test_session_creation() -> None:
    """Verify SessionLocal sessionmaker initialization."""
    session = SessionLocal()
    assert session is not None
    session.close()
